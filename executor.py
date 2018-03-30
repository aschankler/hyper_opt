"""
A modified SSH Executor that provides a different environment for the jobs.
"""

import time
from pylauncher import SSHExecutor, HostLocator, Node
from pylauncher import LauncherException, DebugTraceMsg


class EnvSSHExecutor(SSHExecutor):
    """Modify the execute method to change environment"""
    def __init__(self, env_str='', **kw):
        self.env = env_str
        SSHExecutor.__init__(self, **kw)

    def execute(self, usercommand, **kwargs):
        # find where to execute
        pool = kwargs.pop("pool", None)
        if pool is None:
            raise LauncherException("SSHExecutor needs explicit HostPool")
        if isinstance(pool, Node):
            hostname = pool.hostname
        elif isinstance(pool, HostLocator):
            hostname = pool.firsthost()
        else:
            raise LauncherException("Invalid pool <<%s>>" % str(pool))
        if len(kwargs) > 0:
            raise LauncherException("Unprocessed SSHExecutor args: %s" % str(kwargs))

        # construct the command line with environment, workdir and expiration
        wrapped_line = self.wrap(self.env + usercommand + "\n")
        DebugTraceMsg("Executing << ( %s ) & >> on <<%s>>" % (wrapped_line, hostname),
                      self.debug, prefix="SSH")
        ssh = self.node_client_dict[hostname]
        try:
            stdin, stdout, stderr = \
                ssh.exec_command("( %s ) &" % wrapped_line)
        except:  # old paramiko value? ChannelException:
            DebugTraceMsg("Channel exception; let's see if this blows over", prefix="SSH")
            time.sleep(3)
            ssh.exec_command("( %s ) &" % wrapped_line)
