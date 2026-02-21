from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from model.pad import GstPad


@dataclass(frozen=True)
class GstElement:
    name: str
    pads: Dict[str, GstPad] = field(default_factory=dict)
    pad_links: Dict[str, str] = field(default_factory=dict)  # pad_name -> connected_pad_key
    
    def add_pad(self, pad: GstPad) -> None:
        """Add a pad to this element."""
        object.__setattr__(self, 'pads', {**self.pads, pad.pad_name: pad})
    
    def get_pad(self, pad_name: str) -> Optional[GstPad]:
        """Get a pad by name."""
        return self.pads.get(pad_name)
    
    def link_pad(self, pad_name: str, connected_pad_key: str) -> None:
        """Link a pad to another pad."""
        object.__setattr__(self, 'pad_links', {**self.pad_links, pad_name: connected_pad_key})
    
    def get_connected_pads(self) -> Dict[str, str]:
        """Get all connected pads."""
        return self.pad_links.copy()
    
    def get_src_pads(self) -> Dict[str, GstPad]:
        """Get all source pads."""
        return {name: pad for name, pad in self.pads.items() if pad.pad_name.startswith("src")}
    
    def get_sink_pads(self) -> Dict[str, GstPad]:
        """Get all sink pads."""
        return {name: pad for name, pad in self.pads.items() if pad.pad_name.startswith("sink")}
