"""
Plugin System Manager - Sistema de gerenciamento de plugins com detecção de conflitos
"""

import json
import hashlib
import logging
import re
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from enum import Enum
import importlib.util
import sys
import traceback

from .exceptions import PluginSystemError
from .base import SystemComponentBase


class PluginStatus(Enum):
    """Status do plugin"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONFLICT = "conflict"
    UPDATING = "updating"


class ConflictType(Enum):
    """Tipos de conflitos entre plugins"""
    VERSION_INCOMPATIBLE = "version_incompatible"
    VERSION_INCOMPATIBILITY = "version_incompatibility"  # Alias para compatibilidade com testes
    DEPENDENCY_CONFLICT = "dependency_conflict"
    RESOURCE_CONFLICT = "resource_conflict"
    API_CONFLICT = "api_conflict"
    RUNTIME_CONFLICT = "runtime_conflict"


@dataclass
class PluginVersion:
    """Informações de versão do plugin"""
    major: int
    minor: int
    patch: int
    build: Optional[str] = None
    
    def __init__(self, version_str_or_major: str | int, minor: Optional[int] = None, patch: Optional[int] = None, build: Optional[str] = None):
        """Construtor flexível que aceita string de versão ou componentes separados"""
        if isinstance(version_str_or_major, str):
            # Parse de string no formato "1.2.3" ou "1.2.3-build"
            version_str = version_str_or_major
            if not re.match(r'^\d+\.\d+\.\d+(-\w+)?$', version_str):
                raise ValueError(f"Invalid version format: {version_str}")
            
            parts = version_str.split('-')
            version_part = parts[0]
            build_part = parts[1] if len(parts) > 1 else None
            
            try:
                major, minor, patch = map(int, version_part.split('.'))
            except ValueError:
                raise ValueError(f"Invalid version format: {version_str}")
            
            self.major = major
            self.minor = minor
            self.patch = patch
            self.build = build_part
        else:
            # Construção com componentes separados
            self.major = version_str_or_major
            self.minor = minor or 0
            self.patch = patch or 0
            self.build = build
    
    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.build:
            version += f"-{self.build}"
        return version
    
    def __lt__(self, other: 'PluginVersion') -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __eq__(self, other: 'PluginVersion') -> bool:
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __le__(self, other: 'PluginVersion') -> bool:
        return self < other or self == other
    
    def __gt__(self, other: 'PluginVersion') -> bool:
        return not (self <= other)
    
    def __ge__(self, other: 'PluginVersion') -> bool:
        return self > other or self == other


@dataclass
class PluginDependency:
    """Dependência de plugin"""
    name: str
    version_constraint: str
    required: bool = True
    min_version: Optional[PluginVersion] = None
    max_version: Optional[PluginVersion] = None
    
    def __post_init__(self):
        """Parse do version_constraint para min_version e max_version"""
        if self.version_constraint:
            self._parse_version_constraint()
    
    def _parse_version_constraint(self):
        """Parse de constraint de versão no formato >=1.0.0, <2.0.0, ^1.0.0, etc."""
        constraint = self.version_constraint.strip()
        
        if constraint.startswith('>='):
            version_str = constraint[2:].strip()
            self.min_version = PluginVersion(version_str)
        elif constraint.startswith('<='):
            version_str = constraint[2:].strip()
            self.max_version = PluginVersion(version_str)
        elif constraint.startswith('>'):
            version_str = constraint[1:].strip()
            version = PluginVersion(version_str)
            # Maior que = versão seguinte
            self.min_version = PluginVersion(version.major, version.minor, version.patch + 1)
        elif constraint.startswith('<'):
            version_str = constraint[1:].strip()
            version = PluginVersion(version_str)
            # Menor que = versão anterior
            if version.patch > 0:
                self.max_version = PluginVersion(version.major, version.minor, version.patch - 1)
            elif version.minor > 0:
                self.max_version = PluginVersion(version.major, version.minor - 1, 999)
            else:
                self.max_version = PluginVersion(max(0, version.major - 1), 999, 999)
        elif constraint.startswith('^'):
            # Compatível com major version
            version_str = constraint[1:].strip()
            version = PluginVersion(version_str)
            self.min_version = version
            self.max_version = PluginVersion(version.major + 1, 0, 0)
        else:
            # Versão exata
            self.min_version = PluginVersion(constraint)
            self.max_version = PluginVersion(constraint)
    
    def is_compatible(self, version: PluginVersion) -> bool:
        """Verifica se a versão é compatível com a dependência"""
        if self.min_version and version < self.min_version:
            return False
        if self.max_version and version > self.max_version:
            return False
        return True
    
    def __str__(self) -> str:
        """String representation of dependency"""
        required_str = "required" if self.required else "optional"
        return f"{self.name} ({self.version_constraint}, {required_str})"


@dataclass
class PluginConflict:
    """Representa um conflito entre plugins"""
    conflict_type: ConflictType
    plugin_a: str
    plugin_b: str
    description: str
    plugin1: Optional[str] = None  # Alias para compatibilidade
    plugin2: Optional[str] = None  # Alias para compatibilidade
    severity: str = "medium"  # "low", "medium", "high", "critical"
    resolution_suggestions: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Sincroniza aliases para compatibilidade"""
        if not self.plugin1:
            self.plugin1 = self.plugin_a
        if not self.plugin2:
            self.plugin2 = self.plugin_b
    
    def __str__(self) -> str:
        """String representation of conflict"""
        return f"{self.conflict_type.value.upper()}: {self.plugin_a} <-> {self.plugin_b} ({self.description})"


@dataclass
class PluginMetadata:
    """Metadados do plugin"""
    name: str
    version: PluginVersion
    description: str
    author: str
    dependencies: List[PluginDependency] = field(default_factory=list)
    status: PluginStatus = PluginStatus.INACTIVE
    provides: List[str] = field(default_factory=list)  # APIs/recursos que o plugin fornece
    requires: List[str] = field(default_factory=list)  # Recursos que o plugin precisa
    compatible_versions: List[str] = field(default_factory=list)  # Versões compatíveis do sistema
    signature: Optional[str] = None
    checksum: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of metadata"""
        return f"{self.name} v{self.version} ({self.status.value.upper()})"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Cria metadados a partir de dicionário"""
        version_data = data['version']
        if isinstance(version_data, str):
            version = PluginVersion(version_data)
        else:
            version = PluginVersion(
                major=version_data['major'],
                minor=version_data['minor'],
                patch=version_data['patch'],
                build=version_data.get('build')
            )
        
        dependencies = []
        for dep_data in data.get('dependencies', []):
            if isinstance(dep_data, str):
                # Formato simples: "nome>=1.0.0"
                dependencies.append(PluginDependency(dep_data, ">=0.0.0"))
            else:
                min_ver = None
                max_ver = None
                
                if 'min_version' in dep_data:
                    min_data = dep_data['min_version']
                    if isinstance(min_data, str):
                        min_ver = PluginVersion(min_data)
                    else:
                        min_ver = PluginVersion(min_data['major'], min_data['minor'], min_data['patch'])
                
                if 'max_version' in dep_data:
                    max_data = dep_data['max_version']
                    if isinstance(max_data, str):
                        max_ver = PluginVersion(max_data)
                    else:
                        max_ver = PluginVersion(max_data['major'], max_data['minor'], max_data['patch'])
                
                dependencies.append(PluginDependency(
                    name=dep_data['name'],
                    version_constraint=dep_data.get('version_constraint', '>=0.0.0'),
                    min_version=min_ver,
                    max_version=max_ver,
                    required=dep_data.get('required', True)
                ))
        
        return cls(
            name=data['name'],
            version=version,
            description=data['description'],
            author=data['author'],
            dependencies=dependencies,
            status=PluginStatus(data.get('status', 'inactive')),
            provides=data.get('provides', []),
            requires=data.get('requires', []),
            compatible_versions=data.get('compatible_versions', []),
            signature=data.get('signature'),
            checksum=data.get('checksum')
        )


class PluginConflictDetector:
    """Detector de conflitos entre plugins"""
    
    def __init__(self, config=None):
        """Initialize conflict detector with optional configuration"""
        self._config = config
        self._plugins: Dict[str, PluginMetadata] = {}
        self._conflicts: List[PluginConflict] = []
        self.logger = logging.getLogger(__name__)
    
    def add_plugin(self, metadata: PluginMetadata) -> None:
        """Add a plugin to the detector"""
        if metadata.name in self._plugins:
            raise PluginSystemError(f"Plugin '{metadata.name}' already exists")
        self._plugins[metadata.name] = metadata
        self._update_conflicts()
    
    def remove_plugin(self, plugin_name: str) -> None:
        """Remove a plugin from the detector"""
        if plugin_name not in self._plugins:
            raise PluginSystemError(f"Plugin '{plugin_name}' not found")
        del self._plugins[plugin_name]
        self._update_conflicts()
    
    def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        """Get information about a specific plugin"""
        if plugin_name not in self._plugins:
            raise PluginSystemError(f"Plugin '{plugin_name}' not found")
        
        metadata = self._plugins[plugin_name]
        return {
            "name": metadata.name,
            "version": str(metadata.version),
            "description": metadata.description,
            "author": metadata.author,
            "status": metadata.status.value.upper(),
            "dependencies": [{"name": dep.name, "version_constraint": dep.version_constraint, "required": dep.required} for dep in metadata.dependencies]
        }
    
    def list_plugins(self, status_filter: Optional[PluginStatus] = None) -> Dict[str, PluginMetadata]:
        """List all plugins, optionally filtered by status"""
        if status_filter is None:
            return self._plugins.copy()
        return {name: plugin for name, plugin in self._plugins.items() if plugin.status == status_filter}
    
    def update_plugin_status(self, plugin_name: str, status: PluginStatus) -> None:
        """Update the status of a plugin"""
        if plugin_name not in self._plugins:
            raise PluginSystemError(f"Plugin '{plugin_name}' not found")
        self._plugins[plugin_name].status = status
    
    def clear_plugins(self) -> None:
        """Clear all plugins from the detector"""
        self._plugins.clear()
        self._conflicts.clear()
    
    def validate_plugin_compatibility(self, plugin: PluginMetadata) -> bool:
        """Validate if a plugin is compatible with current plugins"""
        for dependency in plugin.dependencies:
            if dependency.required:
                if dependency.name not in self._plugins:
                    return False
                
                dep_plugin = self._plugins[dependency.name]
                if not dependency.is_compatible(dep_plugin.version):
                    return False
        return True
    
    def detect_conflicts(self, plugins: Optional[Dict[str, PluginMetadata]] = None) -> List[PluginConflict]:
        """Detecta conflitos entre plugins"""
        if plugins is None:
            plugins = self._plugins
        
        conflicts = []
        plugin_list = list(plugins.items())
        
        # Verifica conflitos entre cada par de plugins
        for i, (name1, plugin1) in enumerate(plugin_list):
            for name2, plugin2 in plugin_list[i+1:]:
                plugin_conflicts = self._check_plugin_pair_conflicts(name1, plugin1, name2, plugin2)
                conflicts.extend(plugin_conflicts)
        
        # Verifica conflitos de dependências (dependência ausente ou versão instalada incompatível)
        dependency_conflicts = self._check_dependency_conflicts(plugins)
        conflicts.extend(dependency_conflicts)
        
        # Verifica incompatibilidades de versão cruzadas (restrições mutuamente exclusivas sobre a mesma dependência)
        cross_version_conflicts = self._check_cross_dependency_version_conflicts(plugins)
        conflicts.extend(cross_version_conflicts)
        
        self._conflicts = conflicts
        return conflicts

    def _update_conflicts(self) -> None:
        """Update the internal conflict list"""
        self.detect_conflicts()
    
    def _check_plugin_pair_conflicts(self, name1: str, plugin1: PluginMetadata, 
                                   name2: str, plugin2: PluginMetadata) -> List[PluginConflict]:
        """Verifica conflitos entre um par de plugins"""
        conflicts = []
        
        # Conflito de recursos fornecidos
        common_provides = set(plugin1.provides) & set(plugin2.provides)
        if common_provides:
            conflicts.append(PluginConflict(
                conflict_type=ConflictType.RESOURCE_CONFLICT,
                plugin_a=name1,
                plugin_b=name2,
                description=f"Ambos os plugins fornecem os mesmos recursos: {', '.join(common_provides)}",
                severity="high",
                resolution_suggestions=[
                    "Desabilitar um dos plugins",
                    "Verificar se os plugins podem coexistir",
                    "Usar apenas um plugin por vez"
                ]
            ))
        
        # Conflito de versões incompatíveis (heurística simples baseada em major)
        if self._are_versions_incompatible(plugin1, plugin2):
            conflicts.append(PluginConflict(
                conflict_type=ConflictType.VERSION_INCOMPATIBILITY,
                plugin_a=name1,
                plugin_b=name2,
                description=f"Versões incompatíveis: {plugin1.version} e {plugin2.version}",
                severity="medium",
                resolution_suggestions=[
                    "Atualizar plugins para versões compatíveis",
                    "Verificar documentação de compatibilidade"
                ]
            ))
        
        return conflicts

    def _check_dependency_conflicts(self, plugins: Dict[str, PluginMetadata]) -> List[PluginConflict]:
        """Verifica conflitos de dependências"""
        conflicts = []
        
        for plugin_name, plugin in plugins.items():
            for dependency in plugin.dependencies:
                if dependency.name in plugins:
                    dep_plugin = plugins[dependency.name]
                    if not dependency.is_compatible(dep_plugin.version):
                        conflicts.append(PluginConflict(
                            conflict_type=ConflictType.DEPENDENCY_CONFLICT,
                            plugin_a=plugin_name,
                            plugin_b=dependency.name,
                            description=f"Plugin {plugin_name} requer {dependency.name} "
                                      f"versão compatível, mas encontrou {dep_plugin.version}",
                            severity="critical" if dependency.required else "medium",
                            resolution_suggestions=[
                                f"Atualizar {dependency.name} para versão compatível",
                                f"Atualizar {plugin_name} para versão mais recente",
                                "Verificar requisitos de dependências"
                            ]
                        ))
                elif dependency.required:
                    conflicts.append(PluginConflict(
                        conflict_type=ConflictType.DEPENDENCY_CONFLICT,
                        plugin_a=plugin_name,
                        plugin_b=dependency.name,
                        description=f"Plugin {plugin_name} requer {dependency.name} que não está instalado",
                        severity="critical",
                        resolution_suggestions=[
                            f"Instalar plugin {dependency.name}",
                            f"Desabilitar plugin {plugin_name}",
                            "Verificar dependências obrigatórias"
                        ]
                    ))
        
        return conflicts

    def _check_cross_dependency_version_conflicts(self, plugins: Dict[str, PluginMetadata]) -> List[PluginConflict]:
        """Detecta incompatibilidade de versão entre plugins que impõem restrições conflitantes sobre a mesma dependência.
        
        A lógica considera apenas dependências obrigatórias. Para cada nome de dependência, avalia-se par-a-par se os
        intervalos [min_version, max_version] se sobrepõem. Se não houver sobreposição, um conflito de
        VERSION_INCOMPATIBILITY é registrado entre os dois plugins.
        """
        conflicts: List[PluginConflict] = []
        # Construir índice: dep_name -> lista de (plugin_name, dependency)
        dep_index: Dict[str, List[Tuple[str, PluginDependency]]] = {}
        for plugin_name, plugin in plugins.items():
            for dep in plugin.dependencies:
                if not dep.required:
                    continue
                dep_index.setdefault(dep.name, []).append((plugin_name, dep))
        
        # Helper para limites padrão
        def lower_bound(dep: PluginDependency) -> PluginVersion:
            return dep.min_version or PluginVersion(0, 0, 0)
        
        def upper_bound(dep: PluginDependency) -> PluginVersion:
            # Usa um limite superior muito alto para representar "sem limite"
            return dep.max_version or PluginVersion(999999, 999999, 999999)
        
        # Avaliar conflitos por dependência
        for dep_name, entries in dep_index.items():
            if len(entries) < 2:
                continue
            # Comparar todas as combinações par-a-par
            for i in range(len(entries)):
                name_i, dep_i = entries[i]
                lb_i, ub_i = lower_bound(dep_i), upper_bound(dep_i)
                for j in range(i + 1, len(entries)):
                    name_j, dep_j = entries[j]
                    lb_j, ub_j = lower_bound(dep_j), upper_bound(dep_j)
                    # Interseção de intervalos
                    lb = lb_i if lb_i > lb_j else lb_j
                    ub = ub_i if ub_i < ub_j else ub_j
                    if lb > ub:
                        conflicts.append(PluginConflict(
                            conflict_type=ConflictType.VERSION_INCOMPATIBILITY,
                            plugin_a=name_i,
                            plugin_b=name_j,
                            description=(
                                f"Restrições de versão conflitantes para dependência '{dep_name}': "
                                f"{name_i} requer '{dep_i.version_constraint}', "
                                f"{name_j} requer '{dep_j.version_constraint}'"
                            ),
                            severity="high",
                            resolution_suggestions=[
                                f"Ajustar versões dos plugins {name_i} e/ou {name_j}",
                                f"Atualizar '{dep_name}' para uma versão que atenda ambas as restrições (se possível)",
                                "Consultar documentação de compatibilidade"
                            ]
                        ))
        return conflicts

    def _are_versions_incompatible(self, plugin1: PluginMetadata, plugin2: PluginMetadata) -> bool:
        """Verifica se as versões dos plugins são incompatíveis"""
        # Lógica simples: plugins com major version diferentes podem ser incompatíveis
        return abs(plugin1.version.major - plugin2.version.major) > 1


class PluginVersionManager:
    """Gerenciador de versões de plugins"""
    
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self.logger = logging.getLogger(__name__)
        self.version_history: Dict[str, List[PluginVersion]] = {}
    
    def get_available_versions(self, plugin_name: str) -> List[PluginVersion]:
        """Obtém versões disponíveis de um plugin"""
        return self.version_history.get(plugin_name, [])
    
    def can_update(self, plugin_name: str, current_version: PluginVersion) -> bool:
        """Verifica se o plugin pode ser atualizado"""
        available_versions = self.get_available_versions(plugin_name)
        return any(version > current_version for version in available_versions)
    
    def get_latest_version(self, plugin_name: str) -> Optional[PluginVersion]:
        """Obtém a versão mais recente de um plugin"""
        versions = self.get_available_versions(plugin_name)
        return max(versions) if versions else None
    
    def update_plugin(self, plugin_name: str, target_version: Optional[PluginVersion] = None) -> bool:
        """Atualiza um plugin para a versão especificada ou mais recente"""
        try:
            if target_version is None:
                target_version = self.get_latest_version(plugin_name)
            
            if target_version is None:
                self.logger.error(f"Nenhuma versão disponível para {plugin_name}")
                return False
            
            # Aqui seria implementada a lógica real de atualização
            self.logger.info(f"Atualizando {plugin_name} para versão {target_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar plugin {plugin_name}: {e}")
            return False
    
    def rollback_plugin(self, plugin_name: str, target_version: PluginVersion) -> bool:
        """Faz rollback de um plugin para uma versão anterior"""
        try:
            available_versions = self.get_available_versions(plugin_name)
            if target_version not in available_versions:
                self.logger.error(f"Versão {target_version} não disponível para {plugin_name}")
                return False
            
            # Aqui seria implementada a lógica real de rollback
            self.logger.info(f"Fazendo rollback de {plugin_name} para versão {target_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao fazer rollback do plugin {plugin_name}: {e}")
            return False


class PluginSystemManager(SystemComponentBase):
    """Gerenciador principal do sistema de plugins"""
    
    def __init__(self, plugins_dir: Path, config_manager=None):
        # Para compatibilidade, criamos um config_manager mock se não fornecido
        if config_manager is None:
            from .config import ConfigurationManager
            config_manager = ConfigurationManager()
        
        super().__init__(config_manager, "PluginSystemManager")
        self.plugins_dir = plugins_dir
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        self.loaded_plugins: Dict[str, PluginMetadata] = {}
        self.plugin_status: Dict[str, PluginStatus] = {}
        self.conflict_detector = PluginConflictDetector()
        self.version_manager = PluginVersionManager(plugins_dir)
        self.active_conflicts: List[PluginConflict] = []
        
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> None:
        """Initialize the plugin system"""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info("Plugin system initialized")
    
    def validate_configuration(self) -> None:
        """Validate plugin system configuration"""
        if not self.plugins_dir.exists():
            raise PluginSystemError(f"Plugin directory does not exist: {self.plugins_dir}")
        if not self.plugins_dir.is_dir():
            raise PluginSystemError(f"Plugin path is not a directory: {self.plugins_dir}")
    
    def load_plugin(self, plugin_path: Path) -> bool:
        """Carrega um plugin"""
        try:
            # Carrega metadados do plugin
            metadata_path = plugin_path / "plugin.json"
            if not metadata_path.exists():
                self.logger.error(f"Arquivo plugin.json não encontrado em {plugin_path}")
                return False
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_data = json.load(f)
            
            metadata = PluginMetadata.from_dict(metadata_data)
            
            # Verifica integridade do plugin
            if not self._verify_plugin_integrity(plugin_path, metadata):
                self.logger.error(f"Falha na verificação de integridade do plugin {metadata.name}")
                return False
            
            # Adiciona plugin aos carregados
            self.loaded_plugins[metadata.name] = metadata
            self.plugin_status[metadata.name] = PluginStatus.ACTIVE
            
            self.logger.info(f"Plugin {metadata.name} v{metadata.version} carregado com sucesso")
            
            # Detecta conflitos após carregar
            self._update_conflicts()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar plugin de {plugin_path}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Descarrega um plugin"""
        try:
            if plugin_name not in self.loaded_plugins:
                self.logger.warning(f"Plugin {plugin_name} não está carregado")
                return False
            
            # Remove plugin
            del self.loaded_plugins[plugin_name]
            del self.plugin_status[plugin_name]
            
            # Atualiza conflitos
            self._update_conflicts()
            
            self.logger.info(f"Plugin {plugin_name} descarregado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao descarregar plugin {plugin_name}: {e}")
            return False
    
    def get_conflicts(self) -> List[PluginConflict]:
        """Obtém lista de conflitos atuais"""
        return self.active_conflicts.copy()
    
    def resolve_conflict(self, conflict: PluginConflict, resolution_method: str) -> bool:
        """Resolve um conflito específico"""
        try:
            if resolution_method == "disable_plugin1":
                return self._disable_plugin(conflict.plugin1)
            elif resolution_method == "disable_plugin2":
                return self._disable_plugin(conflict.plugin2)
            elif resolution_method == "update_plugin1":
                return self.version_manager.update_plugin(conflict.plugin1)
            elif resolution_method == "update_plugin2":
                return self.version_manager.update_plugin(conflict.plugin2)
            else:
                self.logger.error(f"Método de resolução desconhecido: {resolution_method}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao resolver conflito: {e}")
            return False
    
    def get_plugin_status(self, plugin_name: str) -> Optional[PluginStatus]:
        """Obtém status de um plugin"""
        return self.plugin_status.get(plugin_name)
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Lista todos os plugins carregados com suas informações"""
        result = {}
        for name, metadata in self.loaded_plugins.items():
            result[name] = {
                'version': str(metadata.version),
                'description': metadata.description,
                'author': metadata.author,
                'status': self.plugin_status[name].value,
                'dependencies': [dep.name for dep in metadata.dependencies],
                'provides': metadata.provides,
                'requires': metadata.requires
            }
        return result
    
    def _verify_plugin_integrity(self, plugin_path: Path, metadata: PluginMetadata) -> bool:
        """Verifica integridade do plugin"""
        try:
            # Verifica checksum se fornecido
            if metadata.checksum:
                calculated_checksum = self._calculate_plugin_checksum(plugin_path)
                if calculated_checksum != metadata.checksum:
                    self.logger.error(f"Checksum inválido para plugin {metadata.name}")
                    return False
            
            # Aqui seria implementada verificação de assinatura digital
            if metadata.signature:
                # Placeholder para verificação de assinatura
                pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na verificação de integridade: {e}")
            return False
    
    def _calculate_plugin_checksum(self, plugin_path: Path) -> str:
        """Calcula checksum do plugin"""
        hasher = hashlib.sha256()
        
        # Calcula hash de todos os arquivos do plugin
        for file_path in plugin_path.rglob('*'):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
        
        return hasher.hexdigest()
    
    def _update_conflicts(self):
        """Atualiza lista de conflitos"""
        self.active_conflicts = self.conflict_detector.detect_conflicts(self.loaded_plugins)
        
        # Atualiza status dos plugins com conflitos
        conflicted_plugins = set()
        for conflict in self.active_conflicts:
            conflicted_plugins.add(conflict.plugin1)
            conflicted_plugins.add(conflict.plugin2)
        
        for plugin_name in conflicted_plugins:
            if plugin_name in self.plugin_status:
                self.plugin_status[plugin_name] = PluginStatus.CONFLICT
    
    def _disable_plugin(self, plugin_name: str) -> bool:
        """Desabilita um plugin"""
        if plugin_name in self.plugin_status:
            self.plugin_status[plugin_name] = PluginStatus.INACTIVE
            self._update_conflicts()
            return True
        return False
    
    def generate_conflict_report(self) -> Dict[str, Any]:
        """Gera relatório detalhado de conflitos"""
        conflicts_by_severity = {}
        for conflict in self.active_conflicts:
            if conflict.severity not in conflicts_by_severity:
                conflicts_by_severity[conflict.severity] = []
            conflicts_by_severity[conflict.severity].append({
                'plugin1': conflict.plugin1,
                'plugin2': conflict.plugin2,
                'type': conflict.conflict_type.value,
                'description': conflict.description,
                'suggestions': conflict.resolution_suggestions,
                'detected_at': conflict.detected_at.isoformat()
            })
        
        return {
            'total_conflicts': len(self.active_conflicts),
            'conflicts_by_severity': conflicts_by_severity,
            'affected_plugins': len(set(c.plugin1 for c in self.active_conflicts) | 
                                 set(c.plugin2 for c in self.active_conflicts)),
            'generated_at': datetime.now().isoformat()
        }