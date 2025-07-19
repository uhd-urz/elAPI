# Architecture and design[^1]

We draw our inspiration from the microkernel architecture[^2] for the overall
architecture principle[^3] and layered architecture for architecture partitioning. There was no strong rationale for
choosing a microkernel architecture over alternatives such as a microservice architecture, other than the desire to
start with something simple that still allows for extensibility. We intend elAPI to serve as the foundation for all
eLabFTW automation solutions. In other words, eLabFTW users should be able to package their automation scripts as
plugins, thereby extending elAPI’s functionality. We refer to this architecture as the "simple microkernel
architecture" (SMA). In the very beginning, SMA was designed for elAPI only. Later we have improved and generalized it
enough to be useful for any software design.

<img src="https://heibox.uni-heidelberg.de/f/32f04718692e4adaa1ff/?dl=1" alt="elAPI simple microkernel architecture" />

## SMA principles

SMA follows most of the principles found in microkernel architecture guidelines with a few additions.

**1. A core system must provide basic functionalities:** The core system principle is adopted straight from the
textbook microkernel architecture principles. In SMA, the core system must provide the basic features. Here, features
that would be considered as basic would depend on the software domain. At a minimum, the core system must enable the
plugin system. The core system in elAPI offers interface style guides, logging functionality, helper functions, OS path
handlers, basic validation abstractions, configuration manager, extended HTTPX API interfaces to communicate with
eLabFTW endpoints, and plugin handlers that enable the entire plugin system. elAPI's core system can be extracted out
and used as the foundation for the SMA implementation for any standalone program.

**2. Interfaces can be flexible across internal plugins:** Typically, a microkernel architecture separates plugins
from the core system entirely. SMA modifies this approach by introducing internal plugins, which reside inside the core
codebase, and external plugins, which can exist anywhere. Both types of plugins can share the same plugin
_interface_. This is also the default with elAPI's SMA implementation. Depending on flexibility preference,
however, having a unique interface or distinct interfaces for internal plugins is also allowed where a unique interface
is enforced upon external plugins.

**3. Internal plugins can be part of the core system:** In SMA, internal plugins can be part of the core system
such that they are meant to be used by external plugins in the same way core system functionalities are used by all
plugins in a typical microkernel architecture. In elAPI, public APIs offered by the internal plugin
_“experiments”_ are meant to be leveraged by external plugins to make updates or advanced modifications to
eLabFTW experiments, among other features. Note, if external plugins are disabled for a SMA implementation, then
internal plugins should not be part of the core system.

**4. Hybrid partitioning is allowed:** SMA recommends technical partitioning for the basic functionality layers. If
domain partitioning is desired, then it is recommended to apply domain partitioning to internal and external plugins.
The combined partitioning helps enforce a design based on strict separation of concerns.

**5. A strict unidirectional dependency must be maintained between technically partitioned layers:** SMA imposes a
dependency invariance between technically partitioned layers. In figure 1, we see a top layer always “depends on” a
bottom layer, or in other words, a bottom layer’s APIs are always exposed to a top layer. This is denoted with an upward
arrow. A layer that sits at the most bottom is an independent layer, as it doesn’t depend on any other layer. The
third-party libraries (typically whose code do not reside in the codebase) do no take part in the invariance, and are
considered floating layers. In that sense, an independent layer is also a floating layer. In elAPI, the `styles` layer
is an independent layer. `styles` layer designate user interface definitions and methods, e.g., the color scheme used by
elAPI CLI. Styles being the independent layer indicates that all dependent layers must adhere to the same UI guidelines.

**6. Plugins need not be independent:** This principle is in line with the third principle. Microkernel
architecture imposes that plugins must be independent, and for good reasons, i.e., to avoid “Big Ball of Mud”[^4]. SMA
still lets the developer decide the rules internal and external plugins should follow.
For example, external plugins can depend on internal plugins (as they are part of the core system). An external plugin
vendor is free to decide that their plugin would depend on another external plugin.

## elAPI SMA layers

We have previously briefly touched on the basic functionality layers elAPI has to offer. In this section, We will peel
back the layers of elAPI and explain the responsibilities of each layer.

**`styles`:** The `styles` layer, an independent layer, is created out of the philosophy that elAPI's CLI UI should be
user-customizable. At the moment though, customization is not available as a feature, but the layer offers UI guidelines
to all layers above. E.g., how a JSON output is formatted and syntax highlighted is defined in this layer. All internal
plugins inherit the same formatting style for JSON output.

**`names`:** Almost every critical constant is defined in this layer. This includes the name of the app itself
_elAPI/elapi_, configuration keys, log file path, etc. Having a single source of truth of constants makes it
quite easy to fork and re-use elAPI's SMA implementation for any other software.

**`loggers`**: The `loggers` layer provides custom methods for logging to all other layers and plugins; hence it sits
quite at the bottom. This custom method doesn't reinvent logging APIs, but rather simply extends upon Python's built-in
logging APIs via composition. E.g., the `STDERR` handler is a [`RichHandler`](https://ludwig.guru/) that enables colored
log output on the CLI. The method by default also logs to a file.

```python
from elapi.loggers import Logger

logger = Logger()
# Logger() returns a pre-configured Python built-in Logger object
logger.error("An error")
```

elAPI `Logger` object is a singleton object.

**`utils`**: As the layer name suggests, this layer mainly hosts utility/helper methods. A few custom exceptions,
special data containers like `MessagesList`, monkey patched fixes for third-party library bugs, etc. are placed here.
`utils` mainly import and expose core utility methods from `core_init/` layer: `get_app_version`, and app-wide callback
methods.

**`path`**: Python comes with the powerful `pathlib` library for handling OS paths. Just like the
`Logger` object, elAPI again extends upon `pathlib.Path` object, and enables some additional path
management features that are quintessential for elAPI. The extended path object is named `ProperPath`, and
its most notable instance methods are: `kind`, `create`, `remove` and `PathException`. `kind` reveals if the
instantiated OS path is a file or a directory. There are some tricky
cases with special files like `/dev/null` which `kind` treats carefully. Based on the file
`kind`, instance methods `create` and `remove` can effectively create and remove any file
or directory. respectively. This avoids boilerplate code needed with `pathlib.Path` to first determine if a
path is a file or a directory. If a `ProperPath` path encounters an exception during an I/O operation (e.g.,
insufficient permission for file creation), the exception is first stored in `PathException` attribute before
being raised. Why? `PathException` offers a fallback mechanism for I/O failures. If writing to a file fails,
it doesn't necessarily mean the entire operation has failed, but it is possible that only the file path is problematic,
and an alternative file path should be tried instead. Plugins like `bill-teams` can iterate over a list of desired paths
for writing data, and if the first path fails, the exception can be caught with the path's `PathException`, and
the plugin can check if stored exception in `PathException` is fatal or non-fatal (e.g., insufficient
permission). If non-fatal, it can move on to the next iteration of file paths and retry writing data. This fallback
approach rescues elAPI from losing data over avoidable I/O issues. In some ways, `PathException` follows the "errors as
values" pattern[^5] from Go.

**`core-validators`**: `core-validators` mainly provides abstract classes and exception for validations that internal
and external plugins are meant to make use of. Despite its name "validators", elAPI's internal plugins actually make use
of validations in the form of parsing—thus adhering to the "parse, don't validate" principle. E.g., The
`PathValidator` provided by `core-validators` converts any valid string to `pathlib.Path`
object. `core-validators` also provides a powerful `Exit` and its subclass `CriticalValidationError` that are meant to
be raised when a critical irrecoverable error is encountered. `Exit` will raise Python
`SystemExit` (quit the program cleanly without showing Python traceback) if it detects elAPI is being run on
the CLI. It will show proper Python traceback if it detects elAPI is being used in a Python script. `Exit` will also
call result callbacks (if any) before exiting.

**`configuration`**: `configuration` layer manages user configuration for elAPI. Under the hood, it mainly utilizes
third-party library [Dynaconf](https://dynaconf.com/) to search and parse user configuration from YAML files.
`configuration` layer also provides
validators for certain configuration key-value pairs found within the configuration file. `configuration` layer also
offers configuration overloading–with which any configuration value defined in a file can be overwritten on the CLI
itself (this CLI option is called `--OC` or `--override-config`). To make this possible, `configuration` layer
implements a
dataclass `ConfigHistory` to store Dynaconf-parsed configuration, a `InspectConfigHistory` class to
allow history inspection, and finally a special configuration value container `MinimalActiveConfiguration`
that stores original and overridden configuration values.

**`api`**: elAPI adopts and extends HTTPX APIs to simplify HTTP requests to eLabFTW. This layer is the bread and
butter of elAPI. It offers a power abstract class `APIRequest` that all other main HTTP requests classes are
made out of. `APIRequest` defines and simplifies connection opening/closing, HTTP client sharing across
multiple calls, and separating asynchronous and synchronous methods.


[^1]: This page has been adapted from an [E-Science-Tage 2025](https://e-science-tage.de/en/downloads) conference paper.
[^2]: https://csse6400.uqcloud.net/handouts/microkernel.pdf
[^3]: https://www.oreilly.com/videos/fundamentals-of-software/9781663728357/
[^4]: http://www.laputan.org/mud/
[^5]: https://jessewarden.com/2021/04/errors-as-values.html
