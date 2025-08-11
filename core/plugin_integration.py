"""
Plugin Integration Mechanisms - Sistema de integração de plugins com runtimes
"""

import json
import logging
from typing import Dict, List, Optional, Any, Type, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum
import importlib.util
import sys
import traceback

from .exceptions import PluginSystemError
from .base import SystemComponentBase, OperationResult
from .plugin_system import PluginMetadata, PluginStatus


class PluginAPIVersion(Enum):
    """Versões da API de plugins suportadas"""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"


class RuntimeType(Enum):
    """Tipos de runtime que podem ser adicionados via plugins"""
    PROGRAMMING_LANGUAGE = "programming_language"
    DEVELOPMENT_TOOL = "development_tool"
    PACKAGE_MANAGER = "package_manager"
    BUILD_SYSTEM = "build_system"
    VERSION_CONTROL = "version_control"
    DATABASE = "database"
    WEB_SERVER = "web_server"
    CONTAINER_RUNTIME = "container_runtime"
    CLOUD_TOOL = "cloud_tool"
    GAME_ENGINE = "game_engine"


@dataclass
class RuntimeDefinition:
    """Definição de um runtime fornecido por plugin"""
    name: str
    version: str
    runtime_type: RuntimeType
    description: str
    detection_methods: List[str]
    installation_methods: List[str]
    validation_commands: List[str]
    environment_variables: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    download_urls: Dict[str, str] = field(default_factory=dict)  # platform -> url
    checksums: Dict[str, str] = field(default_factory=dict)  # platform -> checksum
    installation_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'name': self.name,
            'version': self.version,
            'runtime_type': self.runtime_type.value,
            'description': self.description,
            'detection_methods': self.detection_methods,
            'installation_methods': self.installation_methods,
            'validation_commands': self.validation_commands,
            'environment_variables': self.environment_variables,
            'dependencies': self.dependencies,
            'download_urls': self.download_urls,
            'checksums': self.checksums,
            'installation_notes': self.installation_notes
        }


class PluginAPI(ABC):
    """Interface base para plugins"""
    
    @property
    @abstractmethod
    def api_version(self) -> PluginAPIVersion:
        """Versão da API do plugin"""
        pass
    
    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Nome do plugin"""
        pass
    
    @abstractmethod
    def get_provided_runtimes(self) -> List[RuntimeDefinition]:
        """Retorna lista de runtimes fornecidos pelo plugin"""
        pass
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        """Inicializa o plugin com contexto do sistema"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Limpa recursos do plugin"""
        pass


class PluginAPIV1(PluginAPI):
    """Implementação base da API v1.0 de plugins"""
    
    @property
    def api_version(self) -> PluginAPIVersion:
        return PluginAPIVersion.V1_0
    
    def validate_runtime_definition(self, runtime: RuntimeDefinition) -> bool:
        """Valida definição de runtime"""
        required_fields = ['name', 'version', 'runtime_type', 'description']
        for field in required_fields:
            if not getattr(runtime, field):
                return False
        return True


class PluginAPIV2(PluginAPI):
    """Implementação base da API v2.0 de plugins com recursos avançados"""
    
    @property
    def api_version(self) -> PluginAPIVersion:
        return PluginAPIVersion.V2_0
    
    @abstractmethod
    def get_runtime_dependencies(self, runtime_name: str) -> List[str]:
        """Retorna dependências específicas de um runtime"""
        pass
    
    @abstractmethod
    def can_auto_update(self, runtime_name: str) -> bool:
        """Verifica se o runtime suporta auto-atualização"""
        pass
    
    @abstractmethod
    def get_configuration_schema(self, runtime_name: str) -> Dict[str, Any]:
        """Retorna schema de configuração do runtime"""
        pass


@dataclass
class PluginIntegrationResult:
    """Resultado da integração de um plugin"""
    plugin_name: str
    success: bool
    runtimes_added: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    integration_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'plugin_name': self.plugin_name,
            'success': self.success,
            'runtimes_added': self.runtimes_added,
            'errors': self.errors,
            'warnings': self.warnings,
            'integration_time': self.integration_time.isoformat()
        }


class BackwardCompatibilityManager:
    """Gerenciador de compatibilidade com versões anteriores"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.compatibility_mappings: Dict[str, Dict[str, Any]] = {}
        self.deprecated_apis: Dict[str, str] = {}  # old_api -> new_api
    
    def register_compatibility_mapping(self, old_api: str, new_api: str, 
                                     mapping_function: Callable) -> None:
        """Registra mapeamento de compatibilidade"""
        self.compatibility_mappings[old_api] = {
            'new_api': new_api,
            'mapping_function': mapping_function
        }
        self.deprecated_apis[old_api] = new_api
    
    def is_deprecated(self, api_name: str) -> bool:
        """Verifica se uma API está depreciada"""
        return api_name in self.deprecated_apis
    
    def get_replacement_api(self, deprecated_api: str) -> Optional[str]:
        """Obtém API de substituição para uma API depreciada"""
        return self.deprecated_apis.get(deprecated_api)
    
    def convert_legacy_plugin(self, plugin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Converte plugin legado para formato atual"""
        try:
            # Conversões específicas para diferentes versões
            if 'api_version' not in plugin_data:
                # Plugin muito antigo, assume v1.0
                plugin_data['api_version'] = '1.0'
            
            # Converte estruturas antigas
            if 'runtime_definitions' not in plugin_data and 'runtimes' in plugin_data:
                plugin_data['runtime_definitions'] = plugin_data.pop('runtimes')
            
            # Normaliza tipos de runtime
            if 'runtime_definitions' in plugin_data:
                for runtime in plugin_data['runtime_definitions']:
                    if 'type' in runtime and 'runtime_type' not in runtime:
                        runtime['runtime_type'] = runtime.pop('type')
            
            self.logger.info(f"Converted legacy plugin to current format")
            return plugin_data
            
        except Exception as e:
            self.logger.error(f"Failed to convert legacy plugin: {e}")
            raise PluginSystemError(f"Legacy plugin conversion failed: {e}")


class PluginStatusFeedback:
    """Sistema de feedback de status de plugins"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.status_history: Dict[str, List[Dict[str, Any]]] = {}
        self.feedback_callbacks: List[Callable] = []
    
    def register_feedback_callback(self, callback: Callable) -> None:
        """Registra callback para feedback de status"""
        self.feedback_callbacks.append(callback)
    
    def update_plugin_status(self, plugin_name: str, status: PluginStatus, 
                           message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Atualiza status do plugin com feedback"""
        status_entry = {
            'timestamp': datetime.now().isoformat(),
            'status': status.value,
            'message': message,
            'details': details or {}
        }
        
        if plugin_name not in self.status_history:
            self.status_history[plugin_name] = []
        
        self.status_history[plugin_name].append(status_entry)
        
        # Notifica callbacks
        for callback in self.feedback_callbacks:
            try:
                callback(plugin_name, status, message, details)
            except Exception as e:
                self.logger.error(f"Error in status feedback callback: {e}")
    
    def get_plugin_status_history(self, plugin_name: str) -> List[Dict[str, Any]]:
        """Obtém histórico de status do plugin"""
        return self.status_history.get(plugin_name, [])
    
    def get_current_status(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Obtém status atual do plugin"""
        history = self.get_plugin_status_history(plugin_name)
        return history[-1] if history else None
    
    def generate_status_report(self) -> Dict[str, Any]:
        """Gera relatório de status de todos os plugins"""
        report = {
            'total_plugins': len(self.status_history),
            'plugins': {},
            'generated_at': datetime.now().isoformat()
        }
        
        for plugin_name, history in self.status_history.items():
            current_status = history[-1] if history else None
            report['plugins'][plugin_name] = {
                'current_status': current_status,
                'status_changes': len(history),
                'first_seen': history[0]['timestamp'] if history else None,
                'last_update': history[-1]['timestamp'] if history else None
            }
        
        return report


class RuntimeRegistry:
    """Registro de runtimes fornecidos por plugins"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.registered_runtimes: Dict[str, RuntimeDefinition] = {}
        self.runtime_providers: Dict[str, str] = {}  # runtime_name -> plugin_name
        self.runtime_categories: Dict[RuntimeType, List[str]] = {}
    
    def register_runtime(self, runtime: RuntimeDefinition, plugin_name: str) -> bool:
        """Registra um runtime fornecido por plugin"""
        try:
            if runtime.name in self.registered_runtimes:
                existing_provider = self.runtime_providers[runtime.name]
                if existing_provider != plugin_name:
                    self.logger.warning(
                        f"Runtime {runtime.name} already registered by {existing_provider}, "
                        f"overriding with {plugin_name}"
                    )
            
            self.registered_runtimes[runtime.name] = runtime
            self.runtime_providers[runtime.name] = plugin_name
            
            # Organiza por categoria
            if runtime.runtime_type not in self.runtime_categories:
                self.runtime_categories[runtime.runtime_type] = []
            
            if runtime.name not in self.runtime_categories[runtime.runtime_type]:
                self.runtime_categories[runtime.runtime_type].append(runtime.name)
            
            self.logger.info(f"Registered runtime {runtime.name} from plugin {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register runtime {runtime.name}: {e}")
            return False
    
    def unregister_runtime(self, runtime_name: str) -> bool:
        """Remove registro de um runtime"""
        try:
            if runtime_name not in self.registered_runtimes:
                return False
            
            runtime = self.registered_runtimes[runtime_name]
            
            # Remove das categorias
            if runtime.runtime_type in self.runtime_categories:
                if runtime_name in self.runtime_categories[runtime.runtime_type]:
                    self.runtime_categories[runtime.runtime_type].remove(runtime_name)
            
            # Remove dos registros
            del self.registered_runtimes[runtime_name]
            del self.runtime_providers[runtime_name]
            
            self.logger.info(f"Unregistered runtime {runtime_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister runtime {runtime_name}: {e}")
            return False
    
    def get_runtime(self, runtime_name: str) -> Optional[RuntimeDefinition]:
        """Obtém definição de um runtime"""
        return self.registered_runtimes.get(runtime_name)
    
    def get_runtimes_by_type(self, runtime_type: RuntimeType) -> List[RuntimeDefinition]:
        """Obtém runtimes por tipo"""
        runtime_names = self.runtime_categories.get(runtime_type, [])
        return [self.registered_runtimes[name] for name in runtime_names 
                if name in self.registered_runtimes]
    
    def list_all_runtimes(self) -> Dict[str, Dict[str, Any]]:
        """Lista todos os runtimes registrados"""
        result = {}
        for name, runtime in self.registered_runtimes.items():
            result[name] = {
                'definition': runtime.to_dict(),
                'provider_plugin': self.runtime_providers[name]
            }
        return result
    
    def get_runtime_provider(self, runtime_name: str) -> Optional[str]:
        """Obtém o plugin que fornece um runtime"""
        return self.runtime_providers.get(runtime_name)


class PluginIntegrationManager(SystemComponentBase):
    """Gerenciador de integração de plugins"""
    
    def __init__(self, plugins_dir: Path, config_manager=None):
        if config_manager is None:
            from .config import ConfigurationManager
            config_manager = ConfigurationManager()
        
        super().__init__(config_manager, "PluginIntegrationManager")
        self.plugins_dir = plugins_dir
        self.runtime_registry = RuntimeRegistry()
        self.compatibility_manager = BackwardCompatibilityManager()
        self.status_feedback = PluginStatusFeedback()
        self.loaded_plugin_instances: Dict[str, PluginAPI] = {}
        self.integration_results: Dict[str, PluginIntegrationResult] = {}
        
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> None:
        """Initialize the plugin integration system"""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self._setup_compatibility_mappings()
        self.logger.info("Plugin integration system initialized")
    
    def validate_configuration(self) -> None:
        """Validate plugin integration configuration"""
        if not self.plugins_dir.exists():
            raise PluginSystemError(f"Plugin directory does not exist: {self.plugins_dir}")
        if not self.plugins_dir.is_dir():
            raise PluginSystemError(f"Plugin path is not a directory: {self.plugins_dir}")
    
    def integrate_plugin(self, plugin_path: Path, metadata: PluginMetadata) -> PluginIntegrationResult:
        """Integra um plugin ao sistema"""
        result = PluginIntegrationResult(plugin_name=metadata.name, success=False)
        
        try:
            self.status_feedback.update_plugin_status(
                metadata.name, PluginStatus.UPDATING, "Starting plugin integration"
            )
            
            # Carrega instância do plugin
            plugin_instance = self._load_plugin_instance(plugin_path, metadata)
            if not plugin_instance:
                result.errors.append("Failed to load plugin instance")
                return result
            
            # Verifica compatibilidade da API
            if not self._check_api_compatibility(plugin_instance):
                result.errors.append("Plugin API version not supported")
                return result
            
            # Inicializa plugin
            context = self._create_plugin_context()
            if not plugin_instance.initialize(context):
                result.errors.append("Plugin initialization failed")
                return result
            
            # Registra runtimes fornecidos pelo plugin
            runtimes = plugin_instance.get_provided_runtimes()
            for runtime in runtimes:
                if self._validate_runtime_definition(runtime):
                    if self.runtime_registry.register_runtime(runtime, metadata.name):
                        result.runtimes_added.append(runtime.name)
                    else:
                        result.warnings.append(f"Failed to register runtime {runtime.name}")
                else:
                    result.warnings.append(f"Invalid runtime definition: {runtime.name}")
            
            # Armazena instância do plugin
            self.loaded_plugin_instances[metadata.name] = plugin_instance
            
            result.success = True
            self.status_feedback.update_plugin_status(
                metadata.name, PluginStatus.ACTIVE, 
                f"Plugin integrated successfully. Added {len(result.runtimes_added)} runtimes."
            )
            
        except Exception as e:
            result.errors.append(f"Integration error: {str(e)}")
            self.status_feedback.update_plugin_status(
                metadata.name, PluginStatus.ERROR, f"Integration failed: {str(e)}"
            )
            self.logger.error(f"Plugin integration failed for {metadata.name}: {e}")
        
        self.integration_results[metadata.name] = result
        return result
    
    def remove_plugin_integration(self, plugin_name: str) -> bool:
        """Remove integração de um plugin"""
        try:
            # Remove runtimes fornecidos pelo plugin
            runtimes_to_remove = []
            for runtime_name, provider in self.runtime_registry.runtime_providers.items():
                if provider == plugin_name:
                    runtimes_to_remove.append(runtime_name)
            
            for runtime_name in runtimes_to_remove:
                self.runtime_registry.unregister_runtime(runtime_name)
            
            # Limpa instância do plugin
            if plugin_name in self.loaded_plugin_instances:
                plugin_instance = self.loaded_plugin_instances[plugin_name]
                try:
                    plugin_instance.cleanup()
                except Exception as e:
                    self.logger.warning(f"Plugin cleanup failed for {plugin_name}: {e}")
                
                del self.loaded_plugin_instances[plugin_name]
            
            # Remove resultado de integração
            if plugin_name in self.integration_results:
                del self.integration_results[plugin_name]
            
            self.status_feedback.update_plugin_status(
                plugin_name, PluginStatus.INACTIVE, "Plugin integration removed"
            )
            
            self.logger.info(f"Removed plugin integration for {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove plugin integration for {plugin_name}: {e}")
            return False
    
    def get_available_runtimes(self) -> Dict[str, Dict[str, Any]]:
        """Obtém todos os runtimes disponíveis via plugins"""
        return self.runtime_registry.list_all_runtimes()
    
    def get_runtimes_by_category(self, runtime_type: RuntimeType) -> List[RuntimeDefinition]:
        """Obtém runtimes por categoria"""
        return self.runtime_registry.get_runtimes_by_type(runtime_type)
    
    def get_plugin_status_report(self) -> Dict[str, Any]:
        """Gera relatório de status dos plugins"""
        return self.status_feedback.generate_status_report()
    
    def get_integration_results(self) -> Dict[str, Dict[str, Any]]:
        """Obtém resultados de integração de todos os plugins"""
        return {name: result.to_dict() for name, result in self.integration_results.items()}
    
    def _load_plugin_instance(self, plugin_path: Path, metadata: PluginMetadata) -> Optional[PluginAPI]:
        """Carrega instância do plugin"""
        try:
            # Procura pelo arquivo principal do plugin
            main_file = plugin_path / "main.py"
            if not main_file.exists():
                main_file = plugin_path / f"{metadata.name}.py"
                if not main_file.exists():
                    self.logger.error(f"Plugin main file not found in {plugin_path}")
                    return None
            
            # Carrega módulo do plugin
            spec = importlib.util.spec_from_file_location(metadata.name, main_file)
            if spec is None or spec.loader is None:
                self.logger.error(f"Failed to create module spec for {metadata.name}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Procura pela classe do plugin
            plugin_class = getattr(module, 'Plugin', None)
            if plugin_class is None:
                # Tenta nomes alternativos
                for class_name in [f"{metadata.name}Plugin", "PluginMain", "MainPlugin"]:
                    plugin_class = getattr(module, class_name, None)
                    if plugin_class:
                        break
            
            if plugin_class is None:
                self.logger.error(f"Plugin class not found in {main_file}")
                return None
            
            # Cria instância do plugin
            plugin_instance = plugin_class()
            
            if not isinstance(plugin_instance, PluginAPI):
                self.logger.error(f"Plugin {metadata.name} does not implement PluginAPI")
                return None
            
            return plugin_instance
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin instance for {metadata.name}: {e}")
            return None
    
    def _check_api_compatibility(self, plugin_instance: PluginAPI) -> bool:
        """Verifica compatibilidade da API do plugin"""
        try:
            api_version = plugin_instance.api_version
            
            # Versões suportadas
            supported_versions = [PluginAPIVersion.V1_0, PluginAPIVersion.V1_1, PluginAPIVersion.V2_0]
            
            if api_version not in supported_versions:
                self.logger.error(f"Unsupported plugin API version: {api_version}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check API compatibility: {e}")
            return False
    
    def _create_plugin_context(self) -> Dict[str, Any]:
        """Cria contexto para inicialização do plugin"""
        return {
            'system_version': '1.0.0',
            'supported_api_versions': [v.value for v in PluginAPIVersion],
            'runtime_registry': self.runtime_registry,
            'logger': self.logger,
            'plugins_dir': str(self.plugins_dir)
        }
    
    def _validate_runtime_definition(self, runtime: RuntimeDefinition) -> bool:
        """Valida definição de runtime"""
        try:
            # Campos obrigatórios
            required_fields = ['name', 'version', 'runtime_type', 'description']
            for field in required_fields:
                if not getattr(runtime, field):
                    self.logger.error(f"Runtime {runtime.name} missing required field: {field}")
                    return False
            
            # Valida tipo de runtime
            if not isinstance(runtime.runtime_type, RuntimeType):
                self.logger.error(f"Runtime {runtime.name} has invalid runtime_type")
                return False
            
            # Valida listas obrigatórias
            if not runtime.detection_methods:
                self.logger.warning(f"Runtime {runtime.name} has no detection methods")
            
            if not runtime.installation_methods:
                self.logger.warning(f"Runtime {runtime.name} has no installation methods")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Runtime validation failed for {runtime.name}: {e}")
            return False
    
    def _setup_compatibility_mappings(self):
        """Configura mapeamentos de compatibilidade"""
        # Exemplo de mapeamento para APIs antigas
        def convert_v1_to_v2(old_data):
            # Conversão específica de v1 para v2
            return old_data
        
        self.compatibility_manager.register_compatibility_mapping(
            "plugin_api_v1", "plugin_api_v2", convert_v1_to_v2
        )