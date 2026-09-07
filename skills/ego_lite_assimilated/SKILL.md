# --- DNK-MRH-HEADER ---
# mrh_id: "skills/ego_lite_assimilated/SKILL.md"
# purpose: "Assimilated skill from langchain-ai/ego-lite"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

---
name: "ego_lite-assimilated"
description: "Assimilated patterns and components from langchain-ai/ego-lite"
version: "1.0.0"
category: "research"
assimilated_at: "2026-08-09"
---

# 🌐 ego-lite Assimilated Skill

This skill incorporates SOTA architectural patterns and codebases from LangChain's ego-lite.

## 📌 Scout Analysis (Rick Scout)
Based on the provided code and README, I'll break down the key aspects of the ego-lite CDP browser-automation architecture.

**CLI Initiation**

The CLI is initiated through the `runMain` function, which is exported from the `run.js` file. This function is responsible for setting up the ego-lite runtime and executing the provided command.

Here's a high-level overview of the CLI initiation process:

1. The `runMain` function is called with the provided command as an argument.
2. The function sets up the ego-lite runtime by importing the necessary modules and initializing the `ego` object.
3. The `ego` object is then used to execute the provided command.

**Session Attachment and Auto-Reattachment**

Session attachment and auto-reattachment are critical features of the ego-lite architecture. Here's how they work:

1. When a user initiates a session, the ego-lite runtime creates a new session object.
2. The session object is then attached to the user's browser instance using the Chrome DevTools Protocol (CDP).
3. If the user loses their session (e.g., due to a network issue or browser crash), the ego-lite runtime automatically reattaches to the user's browser instance using the CDP.
4. The reattachment process involves re-establishing the session object and re-syncing the user's browser state.

**Element Resolution**

Element resolution is a critical aspect of the ego-lite architecture, as it enables the runtime to accurately identify and interact with elements on the page. Here's how element resolution works:

1. When a user interacts with an element on the page, the ego-lite runtime uses the CDP to retrieve the element's details (e.g., its ID, class, and attributes).
2. The runtime then uses this information to create a unique identifier for the element, which is stored in the session object.
3. When the user interacts with the element again, the ego-lite runtime uses the stored identifier to retrieve the element's details and perform the desired action.

**Startup Paths**

The ego-lite runtime has several startup paths, which are triggered based on the user's input. Here are some of the key startup paths:

1. **Command-line interface (CLI)**: The CLI is initiated through the `runMain` function, which sets up the ego-lite runtime and executes the provided command.
2. **Browser extension**: The ego-lite browser extension is installed in the user's browser, which allows the runtime to interact with the user's browser instance using the CDP.
3. **CDP**: The ego-lite runtime uses the CDP to interact with the user's browser instance, allowing it to retrieve and manipulate the browser's state.

**Event Queues**

The ego-lite runtime uses event queues to manage the flow of events between the user's browser instance and the runtime. Here's how event queues work:

1. **Event queue creation**: When a user interacts with an element on the page, the ego-lite runtime creates an event queue to manage the flow of events related to that element.
2. **Event queue processing**: The runtime processes the events in the queue, which may involve retrieving the element's details, performing actions on the element, or updating the session object.
3. **Event queue completion**: Once the events in the queue have been processed, the runtime removes the queue and updates the session object accordingly.

**Element Resolver**

The element resolver is a critical component of the ego-lite architecture, as it enables the runtime to accurately identify and interact with elements on the page. Here's how the element resolver works:

1. **Element identification**: When a user interacts with an element on the page, the ego-lite runtime uses the CDP to retrieve the element's details (e.g., its ID, class, and attributes).
2. **Element resolution**: The runtime then uses this information to create a unique identifier for the element, which is stored in the session object.
3. **Element retrieval**: When the user interacts with the element again, the ego-lite runtime uses the stored identifier to retrieve the element's details and perform the desired action.

Overall, the ego-lite CDP browser-automation architecture is designed to provide a seamless and efficient user experience, while also enabling advanced features like session attachment and auto-reattachment.

## 🧬 Sliced Patterns & Component Implementations (Yuriy Slicer)
```python
# author: "DNK-e.com Maksym"

import subprocess
import json
import re

class DNKEgoBrowserAdapter:
    def __init__(self, ego_binary="ego-browser"):
        self.ego_binary = ego_binary
        self.process = None

    def start(self):
        """Start the ego-browser process."""
        self.process = subprocess.Popen(
            [self.ego_binary, "--stdin"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def stop(self):
        """Stop the ego-browser process."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def send_command(self, command):
        """Send a command to the ego-browser process."""
        if not self.process:
            self.start()
        self.process.stdin.write(f"{command}\n".encode())
        self.process.stdin.flush()

    def get_output(self):
        """Get the output from the ego-browser process."""
        if not self.process:
            self.start()
        output, error = self.process.communicate()
        return output.decode().strip()

    def get_snapshot(self):
        """Get a snapshot from the ego-browser process."""
        if not self.process:
            self.start()
        self.send_command("snapshot")
        return self.get_output()

    def run_command(self, command):
        """Run a command in the ego-browser process."""
        if not self.process:
            self.start()
        self.send_command(command)
        return self.get_output()

    def evaluate(self, expression):
        """Evaluate a JavaScript expression in the ego-browser process."""
        if not self.process:
            self.start()
        self.send_command(f"evaluate {expression}")
        return self.get_output()

    def list_task_spaces(self):
        """List all task spaces."""
        return json.loads(self.run_command("listTaskSpaces"))

    def switch_task_space(self, name_or_id):
        """Switch to an existing task space."""
        return json.loads(self.run_command(f"switchTaskSpace {name_or_id}"))

    def is_agent_owned(self, ownership):
        """Check if the agent owns the space."""
        return ownership in ["agent", "agentDelegatedToUser"]

    def find_task_space(self, name_or_id):
        """Find a task space by id or name."""
        task_spaces = self.list_task_spaces()
        for space in task_spaces:
            if space["id"] == name_or_id or space["name"] == name_or_id:
                return space
        return None

# Example usage:
adapter = DNKEgoBrowserAdapter()
adapter.start()
print(adapter.get_snapshot())
print(adapter.list_task_spaces())
print(adapter.switch_task_space("my-task-space"))
print(adapter.is_agent_owned("agent"))
print(adapter.find_task_space("my-task-space"))
adapter.stop()
```

## ⚖️ Governance Standards (Tiffany Governance)
**Ego-Lite Architecture Analysis**

Ego-Lite is a lightweight, containerized architecture for running the Ego CDP (Customer Data Platform) harness and browser integration. It aims to provide a secure, isolated environment for data processing and integration. The architecture consists of the following components:

1. **ego-lite container**: The main container that runs the Ego CDP harness and browser integration.
2. **ego-lite runtime**: A custom runtime that manages the container and provides a secure environment for data processing.
3. **ego-lite plugins**: Optional plugins that can be added to the container to extend its functionality.

**Zero-Host Governance Rules**

To ensure secure and isolated operation of the ego-lite container, we need to establish zero-host governance rules. These rules will prevent host filesystem pollution and ensure that the container operates within its designated boundaries.

**Rule 1: Container Isolation**

* The ego-lite container must run in a separate, isolated environment from the host system.
* The container must not have access to the host filesystem, except for read-only access to the container's configuration files.

**Rule 2: Filesystem Mounting**

* The ego-lite container must use a read-only filesystem mount for its configuration files.
* The container must not have write access to the host filesystem, except for the container's own logs and temporary files.

**Rule 3: Network Isolation**

* The ego-lite container must run in a separate network namespace from the host system.
* The container must not have access to the host network stack, except for communication with other containers in the same network namespace.

**Rule 4: Process Isolation**

* The ego-lite container must run its processes in a separate process namespace from the host system.
* The container must not have access to the host process list, except for its own processes.

**Rule 5: Resource Limitation**

* The ego-lite container must have its resource usage limited to prevent it from consuming excessive resources on the host system.
* The container must not have access to the host system's resources, except for the resources allocated to it by the runtime.

**Rule 6: Logging and Monitoring**

* The ego-lite container must log its activities to a designated log file or log aggregation service.
* The container must provide monitoring and logging capabilities to ensure that its activities can be tracked and audited.

**Explicit Integration Policies**

To ensure seamless integration of the ego-lite container with other systems, we need to establish explicit integration policies. These policies will define how the container interacts with other systems and how data is exchanged between them.

**Policy 1: Data Exchange**

* The ego-lite container must exchange data with other systems using standardized APIs and data formats.
* The container must not have direct access to the data of other systems, except through the APIs and data formats defined in this policy.

**Policy 2: Authentication and Authorization**

* The ego-lite container must authenticate and authorize with other systems using standardized authentication and authorization protocols.
* The container must not have access to the authentication and authorization credentials of other systems, except through the protocols defined in this policy.

**Policy 3: Communication**

* The ego-lite container must communicate with other systems using standardized communication protocols and data formats.
* The container must not have direct access to the communication protocols and data formats of other systems, except through the protocols and data formats defined in this policy.

**Policy 4: Data Storage**

* The ego-lite container must store data in a designated data storage system, such as a database or file system.
* The container must not have direct access to the data storage system of other systems, except through the APIs and data formats defined in this policy.

By establishing these zero-host governance rules and explicit integration policies, we can ensure that the ego-lite container operates securely and isolated from the host system, while also providing seamless integration with other systems.
