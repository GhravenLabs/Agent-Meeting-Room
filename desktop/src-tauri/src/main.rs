#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use std::{
    fs,
    net::{TcpListener, TcpStream},
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::{Arc, Mutex},
    thread,
    time::{Duration, Instant},
};

use tauri::{path::BaseDirectory, Manager, WebviewUrl, WebviewWindowBuilder};

const BACKEND_EXE: &str = "AgentMeetingRoomBackend.exe";
const STARTUP_TIMEOUT: Duration = Duration::from_secs(25);

#[derive(Clone)]
struct BackendProcess(Arc<Mutex<Option<BackendGuard>>>);

struct BackendGuard {
    child: Child,
    #[cfg(target_os = "windows")]
    job: Option<WindowsJob>,
}

#[cfg(target_os = "windows")]
struct WindowsJob(isize);

#[cfg(target_os = "windows")]
impl Drop for WindowsJob {
    fn drop(&mut self) {
        unsafe {
            windows_sys::Win32::Foundation::CloseHandle(self.0 as _);
        }
    }
}

#[cfg(target_os = "windows")]
fn attach_to_kill_on_close_job(child: &Child) -> Result<WindowsJob, String> {
    use std::mem::{size_of, zeroed};
    use std::ptr::null;
    use windows_sys::Win32::Foundation::CloseHandle;
    use windows_sys::Win32::System::JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation,
        SetInformationJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    };
    use windows_sys::Win32::System::Threading::{
        OpenProcess, PROCESS_SET_QUOTA, PROCESS_TERMINATE,
    };

    unsafe {
        let job = CreateJobObjectW(null(), null());
        if job.is_null() {
            return Err("Could not create Windows backend job object.".to_string());
        }

        let mut info: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = zeroed();
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        let set_ok = SetInformationJobObject(
            job,
            JobObjectExtendedLimitInformation,
            &info as *const _ as *const _,
            size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32,
        );
        if set_ok == 0 {
            CloseHandle(job);
            return Err("Could not configure backend job object.".to_string());
        }

        let process = OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, 0, child.id());
        if process.is_null() {
            CloseHandle(job);
            return Err("Could not open backend process for job assignment.".to_string());
        }

        let assign_ok = AssignProcessToJobObject(job, process);
        CloseHandle(process);
        if assign_ok == 0 {
            CloseHandle(job);
            return Err("Could not assign backend process to job object.".to_string());
        }

        Ok(WindowsJob(job as isize))
    }
}

fn guard_backend(child: Child) -> Result<BackendGuard, String> {
    #[cfg(target_os = "windows")]
    {
        let job = attach_to_kill_on_close_job(&child)?;
        return Ok(BackendGuard {
            child,
            job: Some(job),
        });
    }

    #[cfg(not(target_os = "windows"))]
    {
        Ok(BackendGuard { child })
    }
}

fn pick_available_port() -> Result<u16, String> {
    TcpListener::bind("127.0.0.1:0")
        .map_err(|error| format!("Could not allocate a local port: {error}"))?
        .local_addr()
        .map(|addr| addr.port())
        .map_err(|error| format!("Could not inspect local port: {error}"))
}

fn wait_for_backend(port: u16) -> bool {
    let deadline = Instant::now() + STARTUP_TIMEOUT;
    while Instant::now() < deadline {
        if TcpStream::connect(("127.0.0.1", port)).is_ok() {
            return true;
        }
        thread::sleep(Duration::from_millis(250));
    }
    false
}

fn backend_path(app: &tauri::App) -> Result<PathBuf, String> {
    if let Ok(resource_path) = app.path().resolve(BACKEND_EXE, BaseDirectory::Resource) {
        if resource_path.exists() {
            return Ok(resource_path);
        }
    }

    let dev_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("dist")
        .join(BACKEND_EXE);
    if dev_path.exists() {
        return Ok(dev_path);
    }

    Err(format!(
        "{BACKEND_EXE} was not found. Build the backend sidecar first."
    ))
}

fn prepare_data_dir(app: &tauri::App) -> Result<PathBuf, String> {
    let data_dir = app
        .path()
        .app_data_dir()
        .map_err(|error| format!("Could not resolve app data directory: {error}"))?;
    fs::create_dir_all(&data_dir)
        .map_err(|error| format!("Could not create app data directory: {error}"))?;

    let env_example_target = data_dir.join(".env.example");
    if !env_example_target.exists() {
        if let Ok(env_example_source) = app.path().resolve(".env.example", BaseDirectory::Resource)
        {
            let _ = fs::copy(env_example_source, env_example_target);
        }
    }

    Ok(data_dir)
}

fn start_backend(app: &tauri::App, port: u16, data_dir: &PathBuf) -> Result<Child, String> {
    let backend = backend_path(app)?;
    Command::new(backend)
        .env("PORT", port.to_string())
        .env("AGENT_MEETING_ROOM_DESKTOP", "1")
        .env(
            "AGENT_MEETING_ROOM_PARENT_PID",
            std::process::id().to_string(),
        )
        .env("AGENT_MEETING_ROOM_DATA_DIR", data_dir)
        .env("LOCAL_MEMORY_PATH", data_dir.join("meeting_notes"))
        .current_dir(data_dir)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|error| format!("Could not start Agent Meeting Room backend: {error}"))
}

fn stop_backend_tree(mut guard: BackendGuard) {
    #[cfg(target_os = "windows")]
    {
        let _ = Command::new("taskkill")
            .args(["/PID", &guard.child.id().to_string(), "/T", "/F"])
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
    }

    #[cfg(not(target_os = "windows"))]
    {
        let _ = guard.child.kill();
    }

    let _ = guard.child.wait();
    #[cfg(target_os = "windows")]
    {
        guard.job.take();
    }
}

fn build_window(app: &tauri::App, port: u16) -> Result<(), String> {
    let url = format!("http://127.0.0.1:{port}");
    let parsed_url = url
        .parse()
        .map_err(|error| format!("Could not parse backend URL {url}: {error}"))?;

    WebviewWindowBuilder::new(app, "main", WebviewUrl::External(parsed_url))
        .title("Agent Meeting Room")
        .inner_size(1280.0, 860.0)
        .min_inner_size(960.0, 640.0)
        .resizable(true)
        .build()
        .map(|_| ())
        .map_err(|error| format!("Could not create desktop window: {error}"))
}

fn main() {
    let backend_state = BackendProcess(Arc::new(Mutex::new(None)));
    let shutdown_state = backend_state.clone();

    let app = tauri::Builder::default()
        .manage(backend_state.clone())
        .setup(move |app| {
            let port = pick_available_port()?;
            let data_dir = prepare_data_dir(app)?;
            let child = start_backend(app, port, &data_dir)?;

            if !wait_for_backend(port) {
                stop_backend_tree(guard_backend(child)?);
                return Err("Agent Meeting Room backend did not become ready in time.".into());
            }

            *backend_state
                .0
                .lock()
                .map_err(|_| "Could not lock backend process state.")? =
                Some(guard_backend(child)?);
            build_window(app, port)?;
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building Agent Meeting Room desktop app");

    app.run(move |_app_handle, event| {
        if let tauri::RunEvent::Exit = event {
            if let Ok(mut guard) = shutdown_state.0.lock() {
                if let Some(child) = guard.take() {
                    stop_backend_tree(child);
                }
            }
        }
    });
}
