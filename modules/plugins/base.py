class Plugin:
    def __init__(self, core_system):
        self.core = core_system
        self.logger = None # Should be set by subclass

    def get_intents(self):
        """
        Return a dictionary mapping intents to handler methods or descriptions.
        Example: {'install_vscode_extension': self.install_extension}
        """
        return {}

    def execute(self, intent, entities):
        """
        Execute the logic for the given intent.
        """
        raise NotImplementedError
