"""
Graph Storage - Handles saving and managing extracted graph images.
"""
import hashlib
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import json
from datetime import datetime

from .graph_extractor import ExtractedGraph
from ..config import settings


@dataclass
class StoredGraph:
    """Represents a stored graph with file location."""
    id: str
    index: int
    file_path: str
    format: str
    width: Optional[int]
    height: Optional[int]
    caption: str
    cell_index: int
    created_at: str


class GraphStorage:
    """Manages storage of extracted graphs."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.OUTPUT_DIR / "graphs"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.base_dir / "manifest.json"
    
    def store_graphs(self, graphs: List[ExtractedGraph], session_id: str) -> List[StoredGraph]:
        """Store a list of extracted graphs and return storage info."""
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        stored = []
        for graph in graphs:
            stored_graph = self._store_single(graph, session_dir)
            stored.append(stored_graph)
        
        # Save manifest
        self._save_manifest(session_id, stored)
        
        return stored
    
    def _store_single(self, graph: ExtractedGraph, session_dir: Path) -> StoredGraph:
        """Store a single graph image."""
        # Generate unique ID
        hash_input = f"{graph.cell_index}_{graph.index}_{len(graph.image_data)}"
        graph_id = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        
        # Create filename
        filename = f"figure_{graph.index + 1:03d}_{graph_id}.{graph.format}"
        file_path = session_dir / filename
        
        # Write image data
        with open(file_path, "wb") as f:
            f.write(graph.image_data)
        
        return StoredGraph(
            id=graph_id,
            index=graph.index,
            file_path=str(file_path),
            format=graph.format,
            width=graph.width,
            height=graph.height,
            caption=graph.caption,
            cell_index=graph.cell_index,
            created_at=datetime.utcnow().isoformat(),
        )
    
    def _save_manifest(self, session_id: str, graphs: List[StoredGraph]) -> None:
        """Save a manifest of stored graphs."""
        manifest_path = self.base_dir / session_id / "manifest.json"
        manifest = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "graph_count": len(graphs),
            "graphs": [asdict(g) for g in graphs],
        }
        
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    
    def load_manifest(self, session_id: str) -> Optional[Dict]:
        """Load the manifest for a session."""
        manifest_path = self.base_dir / session_id / "manifest.json"
        if not manifest_path.exists():
            return None
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_graph(self, session_id: str, graph_index: int) -> Optional[StoredGraph]:
        """Get a specific graph by index."""
        manifest = self.load_manifest(session_id)
        if not manifest:
            return None
        
        for graph_data in manifest["graphs"]:
            if graph_data["index"] == graph_index:
                return StoredGraph(**graph_data)
        
        return None
    
    def get_all_graphs(self, session_id: str) -> List[StoredGraph]:
        """Get all graphs for a session."""
        manifest = self.load_manifest(session_id)
        if not manifest:
            return []
        
        return [StoredGraph(**g) for g in manifest["graphs"]]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete all graphs for a session."""
        session_dir = self.base_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)
            return True
        return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up sessions older than specified hours."""
        cleaned = 0
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        for session_dir in self.base_dir.iterdir():
            if not session_dir.is_dir():
                continue
            
            manifest_path = session_dir / "manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r") as f:
                        manifest = json.load(f)
                    created = datetime.fromisoformat(manifest["created_at"]).timestamp()
                    if created < cutoff:
                        shutil.rmtree(session_dir)
                        cleaned += 1
                except Exception:
                    pass
        
        return cleaned
    
    def get_graph_bytes(self, session_id: str, graph_index: int) -> Optional[bytes]:
        """Get the raw bytes of a stored graph."""
        graph = self.get_graph(session_id, graph_index)
        if not graph:
            return None
        
        file_path = Path(graph.file_path)
        if not file_path.exists():
            return None
        
        with open(file_path, "rb") as f:
            return f.read()
