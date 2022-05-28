import os


class communicator():
    """
    Object to allow usage of IDP over SSH.
    Firstly, it copies the IDP script to the target location,
    after which it runs the script using the remote IDP exe.
    It needs to copy the file first instead of using input redirection,
    to keep Windows functionality.
    On Linux, a remote executable can be given a local file using input
    redirection. On Windows, this doesn't work correctly.

    Before running the communicate method, all the correct variables should be
    set.

    :var remote_idp_location: the path of the remote folder containing IDP.
    :var filename: the name of the idp file, by default IDPscript.idp.
    :var remote_filename: the name of the idp file to be placed on remote.
    :var local_folder: the current working directory. This is where the
        IDPscript.idp file can be found.
    :var known_hosts_location: the location of the known_hosts file.
    :var address: the remote IP address.
    :var username: the remote username.
    :var password: the remote password.


    TODO: Allow the usage of keys so the password isn't needed.
    """
    def __init__(self):
        self._remote_idp_location = None
        self._filename = "IDPscript.idp"
        self._remote_filename = "IDPscript.idp"
        self._local_folder = os.getcwd()
        self._known_hosts_location = None
        self._address = None
        self._username = None
        self._password = None

    @property
    def remote_idp_location(self):
        return self._remote_idp_location

    @remote_idp_location.setter
    def remote_idp_location(self, value):
        self._remote_idp_location = value

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    def remote_filename(self):
        return self._remote_filename

    @remote_filename.setter
    def remote_filename(self, value):
        self._remote_filename = value

    @property
    def known_hosts_location(self):
        return self._known_hosts_location

    @known_hosts_location.setter
    def known_hosts_location(self, value):
        self._known_hosts_location = value

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = value

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        self._username = value

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = value

    def communicate(self):
        if not self.check_vars():
            print("Not all variables have value.")
            return False
        import paramiko
        local = os.getcwd()
        idp_location = self._remote_idp_location + "/idp"
        remote_file_location = self._remote_idp_location + "/" + \
            self._remote_filename

        ssh = paramiko.SSHClient()
        ssh.load_host_keys(self._known_hosts_location)
        ssh.connect(self._address, username=self._username,
                    password=self._password)

        sftp = ssh.open_sftp()
        if __debug__:
            print("Opened SSH")
        sftp.put(local + "/" + self._filename, remote_file_location)
        sftp.close()

        stdin, stdout, stderr = ssh.exec_command(idp_location
                                                 + " " +
                                                 remote_file_location)
        if __debug__:
            print("Done sending data")
        stdout.channel.recv_exit_status()
        lines = stdout.readlines()
        out = ""
        for line in lines:
            out = out + line
        ssh.close()
        if __debug__:
            print("Closed SSH")
        return out

    def check_vars(self):
        """
        Checks whether all the variables have a value.
        """
        vars_list = [self._remote_idp_location, self._filename,
                     self._remote_filename, self._local_folder,
                     self._known_hosts_location, self._address,
                     self._username, self._password]
        for var in vars_list:
            print(var)
            if var is None:
                return False
        return True
