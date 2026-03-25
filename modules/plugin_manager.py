import os
import importlib
import logging
import pkgutil

class PluginManager:
    def __init__(self, core_system):
        self.core = core_system
        self.plugins = {}
        self.logger = logging.getLogger('PluginManager')
        self.plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')

    def load_plugins(self):
        """Load all plugins from the plugins directory"""
        self.logger.info("Loading plugins...")
        
        # Ensure __init__.py exists in plugins dir
        if not os.path.exists(os.path.join(self.plugin_dir, '__init__.py')):
            with open(os.path.join(self.plugin_dir, '__init__.py'), 'w') as f:
                f.write('')

        # Iterate over modules in the plugins directory
        for _, name, _ in pkgutil.iter_modules([self.plugin_dir]):
            try:
                module = importlib.import_module(f"modules.plugins.{name}")
                
                # Look for a class that ends with 'Plugin'
                for attr_name in dir(module):
                    if attr_name.endswith('Plugin') and attr_name != 'Plugin':
                        plugin_class = getattr(module, attr_name)
                        try:
                            plugin_instance = plugin_class(self.core)
                            self.register_plugin(name, plugin_instance)
                        except Exception as e:
                            self.logger.error(f"Failed to instantiate {attr_name}: {e}")
                            
            except Exception as e:
                self.logger.error(f"Failed to load module {name}: {e}")

    def register_plugin(self, name, plugin):
        self.plugins[name] = plugin
        self.logger.info(f"Registered plugin: {name}")

    def get_plugin_for_intent(self, intent):
        for plugin in self.plugins.values():
            if intent in plugin.get_intents():
                return plugin
        return None
