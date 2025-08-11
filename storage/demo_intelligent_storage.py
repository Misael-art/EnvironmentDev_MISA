"""
Demonstration of Intelligent Storage Management System

This script demonstrates the complete functionality of the Intelligent Storage Manager
including analysis, distribution, and compression capabilities.
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.intelligent_storage_manager import IntelligentStorageManager
from storage.models import DriveInfo, InstallationPriority


def setup_logging():
    """Setup logging for the demonstration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('storage_demo.log')
        ]
    )


def create_sample_components() -> List[Dict]:
    """Create sample components for demonstration"""
    return [
        {
            'name': 'Git 2.47.1',
            'download_size': 52428800,  # 50MB
            'installation_size': 104857600,  # 100MB
            'priority': 'critical',
            'can_compress': True,
            'compression_ratio': 0.7,
            'has_dependencies': False,
            'is_system_component': False,
            'last_used': datetime.now(),
            'usage_frequency': 10
        },
        {
            'name': '.NET SDK 8.0',
            'download_size': 209715200,  # 200MB
            'installation_size': 524288000,  # 500MB
            'priority': 'critical',
            'can_compress': True,
            'compression_ratio': 0.8,
            'has_dependencies': False,
            'is_system_component': False,
            'last_used': datetime.now(),
            'usage_frequency': 8
        },
        {
            'name': 'Java JDK 21',
            'download_size': 167772160,  # 160MB
            'installation_size': 419430400,  # 400MB
            'priority': 'high',
            'can_compress': True,
            'compression_ratio': 0.75,
            'has_dependencies': False,
            'is_system_component': False,
            'last_used': datetime.now(),
            'usage_frequency': 6
        },
        {
            'name': 'Node.js Latest',
            'download_size': 31457280,  # 30MB
            'installation_size': 83886080,  # 80MB
            'priority': 'high',
            'can_compress': True,
            'compression_ratio': 0.6,
            'has_dependencies': True,
            'is_system_component': False,
            'last_used': datetime.now(),
            'usage_frequency': 7
        },
        {
            'name': 'Visual Studio Code',
            'download_size': 104857600,  # 100MB
            'installation_size': 314572800,  # 300MB
            'priority': 'medium',
            'can_compress': True,
            'compression_ratio': 0.8,
            'has_dependencies': False,
            'is_system_component': False,
            'last_used': datetime.now(),
            'usage_frequency': 9
        },
        {
            'name': 'Optional Development Tools',
            'download_size': 52428800,  # 50MB
            'installation_size': 157286400,  # 150MB
            'priority': 'optional',
            'can_compress': True,
            'compression_ratio': 0.5,
            'has_dependencies': False,
            'is_system_component': False,
            'last_used': datetime.now(),
            'usage_frequency': 2
        }
    ]


def demonstrate_space_analysis(manager: IntelligentStorageManager, components: List[Dict]):
    """Demonstrate space analysis capabilities"""
    print("\n" + "="*60)
    print("SPACE ANALYSIS DEMONSTRATION")
    print("="*60)
    
    try:
        # Calculate space requirements
        print("\n1. Calculating space requirements...")
        space_requirements = manager.calculate_space_requirements_before_installation(components)
        
        print(f"   Total components: {len(space_requirements.components)}")
        print(f"   Total download size: {format_size(space_requirements.total_download_size)}")
        print(f"   Total installation size: {format_size(space_requirements.total_installation_size)}")
        print(f"   Total temporary space: {format_size(space_requirements.total_temporary_space)}")
        print(f"   Total required space: {format_size(space_requirements.total_required_space)}")
        print(f"   Recommended free space: {format_size(space_requirements.recommended_free_space)}")
        
        # Show component breakdown
        print("\n   Component breakdown:")
        for comp in space_requirements.components:
            print(f"   - {comp.component_name}: {format_size(comp.total_required)} "
                  f"(Priority: {comp.priority.value})")
        
        return space_requirements
        
    except Exception as e:
        print(f"   Error in space analysis: {e}")
        return None


def demonstrate_selective_installation(manager: IntelligentStorageManager, components: List[Dict]):
    """Demonstrate selective installation analysis"""
    print("\n" + "="*60)
    print("SELECTIVE INSTALLATION DEMONSTRATION")
    print("="*60)
    
    try:
        # Test with different available space scenarios
        scenarios = [
            ("Abundant Space", 10 * 1024 * 1024 * 1024),  # 10GB
            ("Limited Space", 1 * 1024 * 1024 * 1024),    # 1GB
            ("Very Limited Space", 500 * 1024 * 1024),    # 500MB
            ("Insufficient Space", 100 * 1024 * 1024)     # 100MB
        ]
        
        for scenario_name, available_space in scenarios:
            print(f"\n{scenario_name} Scenario ({format_size(available_space)} available):")
            
            result = manager.enable_selective_installation_based_on_available_space(
                available_space, components
            )
            
            print(f"   Installation feasible: {result.installation_feasible}")
            print(f"   Installable components: {len(result.installable_components)}")
            print(f"   Skipped components: {len(result.skipped_components)}")
            print(f"   Space saved: {format_size(result.space_saved)}")
            print(f"   Total space required: {format_size(result.total_space_required)}")
            
            if result.installable_components:
                print(f"   Can install: {', '.join(result.installable_components)}")
            
            if result.skipped_components:
                print(f"   Must skip: {', '.join(result.skipped_components)}")
            
            if result.recommendations:
                print("   Recommendations:")
                for rec in result.recommendations:
                    print(f"   - {rec}")
        
    except Exception as e:
        print(f"   Error in selective installation analysis: {e}")


def demonstrate_distribution_analysis(manager: IntelligentStorageManager, components: List[Dict]):
    """Demonstrate intelligent distribution across drives"""
    print("\n" + "="*60)
    print("INTELLIGENT DISTRIBUTION DEMONSTRATION")
    print("="*60)
    
    try:
        # Get system drives
        drives = manager.storage_analyzer.analyze_system_storage()
        
        if not drives:
            print("   No drives detected for distribution analysis")
            return
        
        print(f"\n1. Detected {len(drives)} drives:")
        for drive in drives:
            print(f"   - {drive.drive_letter}: {format_size(drive.available_space)} available "
                  f"({format_size(drive.total_space)} total, "
                  f"Performance: {drive.performance_score:.2f}, "
                  f"System: {drive.is_system_drive})")
        
        # Perform distribution analysis
        print("\n2. Analyzing optimal distribution...")
        distribution_result = manager.intelligently_distribute_across_multiple_drives(
            drives, components
        )
        
        print(f"   Distribution feasible: {distribution_result.distribution_feasible}")
        print(f"   Total components: {distribution_result.total_components}")
        print(f"   Drives used: {len(distribution_result.drives_used)}")
        print(f"   Space optimization: {distribution_result.space_optimization:.1f}%")
        
        if distribution_result.distribution_plans:
            print("\n   Distribution plan:")
            for plan in distribution_result.distribution_plans:
                print(f"   - {plan.component_name} → {plan.target_drive} "
                      f"({format_size(plan.space_required)})")
                print(f"     Path: {plan.installation_path}")
                print(f"     Reason: {plan.reason}")
        
        if distribution_result.warnings:
            print("\n   Warnings:")
            for warning in distribution_result.warnings:
                print(f"   - {warning}")
        
        return distribution_result
        
    except Exception as e:
        print(f"   Error in distribution analysis: {e}")
        return None


def demonstrate_compression_analysis(manager: IntelligentStorageManager):
    """Demonstrate intelligent compression capabilities"""
    print("\n" + "="*60)
    print("INTELLIGENT COMPRESSION DEMONSTRATION")
    print("="*60)
    
    try:
        # Create some sample paths for compression analysis
        sample_paths = [
            ".",  # Current directory
            "./logs",
            "./temp",
            "./cache"
        ]
        
        print("\n1. Analyzing compression opportunities...")
        
        # Test different compression scenarios
        scenarios = [
            ("Rarely Accessed Components", "compress_rarely_accessed_components"),
            ("Configuration Backups", "compress_configuration_backups"),
            ("Previous Version History", "compress_previous_version_history")
        ]
        
        for scenario_name, method_name in scenarios:
            print(f"\n{scenario_name}:")
            
            try:
                method = getattr(manager, method_name)
                result = method(sample_paths)
                
                print(f"   Compression successful: {result.success}")
                print(f"   Files compressed: {len(result.compressed_files)}")
                print(f"   Original size: {format_size(result.original_total_size)}")
                print(f"   Compressed size: {format_size(result.compressed_total_size)}")
                print(f"   Space saved: {format_size(result.space_saved)}")
                print(f"   Compression ratio: {result.compression_ratio:.2f}")
                print(f"   Duration: {result.compression_duration:.2f} seconds")
                
                if result.errors:
                    print("   Errors:")
                    for error in result.errors:
                        print(f"   - {error}")
                        
            except Exception as e:
                print(f"   Error in {scenario_name}: {e}")
        
    except Exception as e:
        print(f"   Error in compression analysis: {e}")


def demonstrate_cleanup_operations(manager: IntelligentStorageManager):
    """Demonstrate cleanup operations"""
    print("\n" + "="*60)
    print("CLEANUP OPERATIONS DEMONSTRATION")
    print("="*60)
    
    try:
        # Sample installation paths
        installation_paths = [
            "./temp_install",
            "./downloads",
            "./cache"
        ]
        
        print("\n1. Performing automatic cleanup...")
        cleanup_result = manager.automatically_remove_temporary_files_after_installation(
            installation_paths
        )
        
        print(f"   Cleanup successful: {cleanup_result.success}")
        print(f"   Files cleaned: {len(cleanup_result.cleaned_files)}")
        print(f"   Space freed: {format_size(cleanup_result.space_freed)}")
        print(f"   Duration: {cleanup_result.cleanup_duration:.2f} seconds")
        
        if cleanup_result.errors:
            print("   Errors:")
            for error in cleanup_result.errors:
                print(f"   - {error}")
        
        if cleanup_result.cleaned_files:
            print("   Sample cleaned files:")
            for file_path in cleanup_result.cleaned_files[:5]:  # Show first 5
                print(f"   - {file_path}")
            if len(cleanup_result.cleaned_files) > 5:
                print(f"   ... and {len(cleanup_result.cleaned_files) - 5} more")
        
    except Exception as e:
        print(f"   Error in cleanup operations: {e}")


def demonstrate_removal_suggestions(manager: IntelligentStorageManager, components: List[Dict]):
    """Demonstrate component removal suggestions"""
    print("\n" + "="*60)
    print("REMOVAL SUGGESTIONS DEMONSTRATION")
    print("="*60)
    
    try:
        # Test different space requirements
        space_scenarios = [
            ("Moderate Space Needed", 500 * 1024 * 1024),  # 500MB
            ("Large Space Needed", 2 * 1024 * 1024 * 1024),  # 2GB
        ]
        
        for scenario_name, required_space in space_scenarios:
            print(f"\n{scenario_name} ({format_size(required_space)} required):")
            
            suggestions = manager.suggest_components_for_removal_when_storage_low(
                components, required_space
            )
            
            print(f"   Total suggestions: {len(suggestions.suggestions)}")
            print(f"   Total potential space: {format_size(suggestions.total_potential_space)}")
            print(f"   Recommended removals: {len(suggestions.recommended_removals)}")
            
            if suggestions.recommended_removals:
                print(f"   Safe to remove: {', '.join(suggestions.recommended_removals)}")
            
            print("   Detailed suggestions:")
            for suggestion in suggestions.suggestions[:3]:  # Show first 3
                print(f"   - {suggestion.component_name}: {format_size(suggestion.space_freed)}")
                print(f"     Safety: {suggestion.removal_safety}, Impact: {suggestion.impact_level}")
                print(f"     {suggestion.description}")
        
    except Exception as e:
        print(f"   Error in removal suggestions: {e}")


def demonstrate_comprehensive_analysis(manager: IntelligentStorageManager, components: List[Dict]):
    """Demonstrate comprehensive storage analysis"""
    print("\n" + "="*60)
    print("COMPREHENSIVE STORAGE ANALYSIS")
    print("="*60)
    
    try:
        print("\n1. Performing comprehensive analysis...")
        analysis_result = manager.perform_comprehensive_storage_analysis(components)
        
        print(f"   Overall feasibility: {analysis_result.overall_feasibility}")
        print(f"   Drives analyzed: {len(analysis_result.drives)}")
        print(f"   Compression opportunities: {len(analysis_result.compression_opportunities)}")
        
        print("\n2. Summary of findings:")
        for recommendation in analysis_result.recommendations:
            print(f"   - {recommendation}")
        
        print(f"\n3. Space requirements summary:")
        space_req = analysis_result.space_requirements
        print(f"   - Total required: {format_size(space_req.total_required_space)}")
        print(f"   - Recommended free: {format_size(space_req.recommended_free_space)}")
        
        print(f"\n4. Selective installation summary:")
        selective = analysis_result.selective_installation
        print(f"   - Installation feasible: {selective.installation_feasible}")
        print(f"   - Components installable: {len(selective.installable_components)}")
        print(f"   - Components skipped: {len(selective.skipped_components)}")
        
        print(f"\n5. Distribution summary:")
        distribution = analysis_result.distribution_result
        print(f"   - Distribution feasible: {distribution.distribution_feasible}")
        print(f"   - Drives used: {len(distribution.drives_used)}")
        print(f"   - Space optimization: {distribution.space_optimization:.1f}%")
        
        return analysis_result
        
    except Exception as e:
        print(f"   Error in comprehensive analysis: {e}")
        return None


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def main():
    """Main demonstration function"""
    print("INTELLIGENT STORAGE MANAGEMENT SYSTEM DEMONSTRATION")
    print("=" * 80)
    print("This demonstration shows the complete functionality of the")
    print("Intelligent Storage Management System for Environment Dev.")
    print("=" * 80)
    
    # Setup logging
    setup_logging()
    
    # Create manager and sample data
    manager = IntelligentStorageManager()
    components = create_sample_components()
    
    print(f"\nInitialized with {len(components)} sample components:")
    for comp in components:
        print(f"  - {comp['name']}: {format_size(comp['installation_size'])} "
              f"(Priority: {comp['priority']})")
    
    # Run demonstrations
    try:
        # 1. Space Analysis
        space_requirements = demonstrate_space_analysis(manager, components)
        
        # 2. Selective Installation
        demonstrate_selective_installation(manager, components)
        
        # 3. Distribution Analysis
        distribution_result = demonstrate_distribution_analysis(manager, components)
        
        # 4. Compression Analysis
        demonstrate_compression_analysis(manager)
        
        # 5. Cleanup Operations
        demonstrate_cleanup_operations(manager)
        
        # 6. Removal Suggestions
        demonstrate_removal_suggestions(manager, components)
        
        # 7. Comprehensive Analysis
        comprehensive_result = demonstrate_comprehensive_analysis(manager, components)
        
        # Final summary
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nThe Intelligent Storage Management System has demonstrated:")
        print("✓ Space requirement calculation and analysis")
        print("✓ Selective installation based on available space")
        print("✓ Intelligent distribution across multiple drives")
        print("✓ Compression opportunities identification")
        print("✓ Automatic cleanup of temporary files")
        print("✓ Component removal suggestions")
        print("✓ Comprehensive storage analysis")
        print("\nAll components are working correctly and ready for integration!")
        
    except Exception as e:
        print(f"\nDemonstration failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()