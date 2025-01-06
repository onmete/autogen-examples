import subprocess


def list_pods(namespace: str) -> str:
    """Lists pods via oc cli in the given namespace.
    
    Example output:
    NAME       READY   STATUS    RESTARTS   AGE
    pod1       1/1     Running   0          1d
    pod2       0/1     Failed    2          38m
    """
    return r"""
    NAME       READY   STATUS    RESTARTS   AGE
    pod1       1/1     Running   0          1d
    pod2       0/1     Failed    2          38m  
    """


def pod_logs(namespace: str, pod_name: str) -> str:
    """Gathers logs for the given pod in the given namespace."""
    return r"""
some log
something happens here
and here too   
"""


def openshift_cli(command: str) -> str:
    """Executes the given oc cli command.

    This tool works ONLY for the `oc` CLI commands, it CAN't execute any other commands.
    
    Args:
        commands: list of strings, the commands to execute

    Example:
    I want to execute `oc get pods -n ols-test`.
    The input parameter `commands` should be `oc get pods -n ols-test`.

    Returns the ouput of the given `oc` command.
    """
    args = command.split(" ")
    if args[0] == "oc":
        args = args[1:]
    print(f"DEBUG: Executing oc command with args: {args}")
    try:
        res = subprocess.run(
            ["oc", *args],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        return f"Error running oc command {args}: {e}, stdout: {e.output}, stderr: {e.stderr}"
    return str(res)