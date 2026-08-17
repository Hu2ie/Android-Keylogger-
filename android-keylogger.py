import asyncio
import sys
import os
import xml.etree.ElementTree as ET
from typing import Optional

class AndroidUIObserver:
    """Professional asynchronous UI hierarchy analyzer for Android devices via ADB."""
    
    def __init__(self, pull_interval: float = 0.5):
        self.pull_interval = pull_interval
        self.last_signature: Optional[int] = None

    async def _execute_adb_command(self, *args: str) -> str:
        """Low-level asynchronous call to the ADB subsystem."""
        proc = await asyncio.create_subprocess_exec(
            'adb', *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return stdout.decode('utf-8', errors='ignore').strip()

    async def dump_ui_hierarchy(self) -> Optional[str]:
        """Captures the current UI hierarchy tree using the UI Automator Framework."""
        dump_res = await self._execute_adb_command("shell", "uiautomator", "dump", "/data/local/tmp/uidump.xml")
        if "UI hierchary dumped to" not in dump_res:
            return None
        
        xml_content = await self._execute_adb_command("shell", "cat", "/data/local/tmp/uidump.xml")
        return xml_content

    def parse_interactive_nodes(self, xml_data: str) -> None:
        """Recursively parses XML layout nodes to identify clickable elements and inputs."""
        try:
            root = ET.fromstring(xml_data)
            nodes = root.findall(".//node[@clickable='true']")
            
            for node in nodes:
                resource_id = node.get('resource-id', '')
                class_name = node.get('class', '').split('.')[-1]
                text = node.get('text', '')
                bounds = node.get('bounds', '')

                if "EditText" in class_name or "Button" in class_name:
                    print(f"  [NODE_DETECTION] Type: {class_name:12} | ID: {resource_id:30} | Value: '{text}' | Area: {bounds}")
        except ET.ParseError:
            pass

    async def start_monitor(self):
        """Main async loop tracking runtime display state modifications."""
        print(f"[#] Initializing AndroidUIObserver core engine... [Polling: {self.pull_interval}s]")
        print("[#] Awaiting system responses on USB bus architecture...\n")
        
        try:
            while True:
                xml_data = await self.dump_ui_hierarchy()
                if not xml_data:
                    await asyncio.sleep(self.pull_interval)
                    continue

                current_signature = hash(xml_data)
                if current_signature != self.last_signature:
                    print(f"\n[CONTEXT_SWITCH] --- Runtime Layout Modified (SIG: {current_signature}) ---")
                    self.parse_interactive_nodes(xml_data)
                    self.last_signature = current_signature

                await asyncio.sleep(self.pull_interval)
                
        except asyncio.CancelledError:
            print("\n[-] UI Monitoring session terminated correctly.")

if __name__ == "__main__":
    if sys.platform == "win32":
        os.system('chcp 65001 > nul')
        
    observer = AndroidUIObserver(pull_interval=0.5)
    try:
        asyncio.run(observer.start_monitor())
    except KeyboardInterrupt:
        pass

