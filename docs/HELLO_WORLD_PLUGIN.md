# Hello World Plugin

This example shows how to publish a minimal plugin that works with both the backend lifecycle hooks and the frontend UI loader.

## Backend hello world

1. Create a Python package with an entrypoint in `pyproject.toml`:

```toml
[project.entry-points."hisper.plugins"]
hello_world = "hello_world_plugin:HelloWorldPlugin"
```

2. Implement the plugin class using the base interface:

```python
from hisper.app.plugins import BasePlugin
from hisper.app.models.plugin import PluginManifest, PluginCapability
from fastapi import APIRouter


class HelloWorldPlugin(BasePlugin):
    def __init__(self):
        self.manifest = PluginManifest(
            identifier="hello-world",
            name="Hello World",
            version="1.0.0",
            description="Demonstrates plugin lifecycle hooks",
            plugin_type="discovery",
            capabilities=[],
            frontend={
                "panels": [
                    {
                        "id": "hello-panel",
                        "title": "Hello from a plugin",
                        "route": "/plugins/hello",
                        "description": "Shows a simple iframe panel",
                        "iframeUrl": "https://example.com/hello",
                    }
                ]
            },
        )

    def capability_descriptors(self):
        return [
            PluginCapability(kind="discovery", description="Adds a demo discovery source"),
            PluginCapability(kind="analytics", description="Reports basic metrics"),
        ]

    def register_routes(self):
        router = APIRouter()

        @router.get("/hello-plugin")
        def hello():
            return {"message": "Hello from a plugin"}

        return [router]
```

3. Install the plugin in the same environment as Hisper, restart the server, and it will be automatically discovered and recorded in the plugin registry.

## Manifest-only UI extension

To publish only a UI panel without Python code, drop a file that ends with `.plugin.json` into any directory listed in `PLUGIN_MANIFEST_DIRS`:

```json
{
  "identifier": "hello-ui",
  "name": "Hello UI",
  "version": "1.0.0",
  "description": "Adds a friendly dashboard panel",
  "plugin_type": "ui",
  "capabilities": [
    {"kind": "ui", "description": "Adds a hello world iframe"}
  ],
  "frontend": {
    "panels": [
      {
        "id": "hello-ui-panel",
        "title": "Hello UI",
        "route": "/plugins/hello-ui",
        "iframeUrl": "https://example.com/hello-ui"
      }
    ]
  }
}
```

The frontend plugin loader will render the new panel under navigation with sandboxed iframe isolation and optional permission gates.
