"""
Document Server CLI Client (Refactored)
"""

from .session import SessionManager
from .files import FileManager
from .folders import FolderManager

class DocumentServerCLI:
    """Client for interacting with Document Server backend (refactored)"""
    def __init__(self, base_url: str = None):
        self.session_manager = SessionManager(base_url)
        self.file_manager = FileManager(self.session_manager)
        self.folder_manager = FolderManager(self.session_manager)

    # Properties to access current directory state
    @property
    def current_folder_id(self):
        return self.folder_manager.current_folder_id
    
    @property
    def current_folder_name(self):
        return self.folder_manager.current_folder_name

    # Session methods
    def login(self, username: str, password: str) -> bool:
        return self.session_manager.login(username, password)

    def register(self, username: str, email: str, password: str, grade: int = 33) -> bool:
        return self.session_manager.register(username, email, password, grade)

    def logout(self) -> bool:
        # Reset current directory state
        self.folder_manager.current_folder_id = None
        self.folder_manager.current_folder_name = None
        return self.session_manager.logout()

    def is_session_valid(self) -> bool:
        return self.session_manager.is_session_valid()

    def get_current_user(self):
        return self.session_manager.get_current_user()

    def show_login_status(self):
        return self.session_manager.show_login_status()

    def list_sessions(self):
        return self.session_manager.list_sessions()

    def switch_user(self, username: str) -> bool:
        return self.session_manager.switch_user(username)

    # File methods
    def upload(self, file_path: str) -> bool:
        return self.file_manager.upload(file_path, self.current_folder_id, self.current_folder_name)

    def download(self, filename: str, output_path: str = None) -> bool:
        return self.file_manager.download(filename, output_path)

    def delete(self, filename: str) -> bool:
        return self.file_manager.delete(filename, self.current_folder_name)

    # Folder methods
    def create_folder(self, folder_name: str, parent_id: int = None) -> bool:
        return self.folder_manager.create_folder(folder_name, parent_id)

    def delete_folder_by_name(self, folder_name: str) -> bool:
        return self.folder_manager.delete_folder_by_name(folder_name)

    def delete_folder(self, folder_id: int) -> bool:
        return self.folder_manager.delete_folder(folder_id)

    def show_folder_tree(self) -> bool:
        return self.folder_manager.show_folder_tree()

    def change_directory(self, folder_name: str) -> bool:
        return self.folder_manager.change_directory(folder_name)

    def show_current_directory(self) -> bool:
        return self.folder_manager.show_current_directory()

    def list_files_in_folder(self, folder_name: str = None) -> bool:
        return self.folder_manager.list_files_in_folder(folder_name)

    def move_file(self, filename: str, folder_name: str) -> bool:
        return self.folder_manager.move_file(filename, folder_name)

    def list_folders(self) -> bool:
        return self.folder_manager.list_folders()

    def get_folder_id_by_name(self, folder_name: str):
        return self.folder_manager.get_folder_id_by_name(folder_name) 