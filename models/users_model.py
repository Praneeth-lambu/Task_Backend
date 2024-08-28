class UserModel:
    def __init__(self, username,email, password_hash, role):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
