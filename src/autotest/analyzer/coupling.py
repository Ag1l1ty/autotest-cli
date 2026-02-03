"""Module coupling analyzer - builds import graph and calculates coupling metrics."""

from __future__ import annotations

from pathlib import Path

from autotest.models.analysis import CouplingInfo, ModuleMetrics


def calculate_coupling(modules: list[ModuleMetrics]) -> list[CouplingInfo]:
    """Calculate coupling metrics for all modules."""
    # Build import graph
    module_paths = {str(m.file_path) for m in modules}
    import_map: dict[str, set[str]] = {}
    
    for module in modules:
        import_map[str(module.file_path)] = set()
        for imp in module.imports:
            # Try to resolve import to a module path
            for mp in module_paths:
                if imp.replace(".", "/") in mp or imp.split(".")[-1] in Path(mp).stem:
                    import_map[str(module.file_path)].add(mp)

    # Calculate afferent (incoming) and efferent (outgoing) coupling
    coupling_data: list[CouplingInfo] = []

    for module in modules:
        mp = str(module.file_path)
        
        # Efferent: what this module depends on
        efferent = len(import_map.get(mp, set()))
        
        # Afferent: what depends on this module
        afferent = sum(1 for deps in import_map.values() if mp in deps)
        
        # Instability: Ce / (Ca + Ce), 0 = stable, 1 = unstable
        total = afferent + efferent
        instability = efferent / total if total > 0 else 0.0

        # Update module with reverse deps
        module.imported_by = [
            path for path, deps in import_map.items() if mp in deps
        ]

        coupling_data.append(CouplingInfo(
            module_path=module.file_path,
            afferent_coupling=afferent,
            efferent_coupling=efferent,
            instability=round(instability, 3),
        ))

    return coupling_data
