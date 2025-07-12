haggis
======

This is a library of general purpose utility functions and classes written in
Python. Much of this code is intended to support the imprint project
<https://gitlab.com/madphysicist/imprint>. The modules of this library are
more-or-less standalone utilities, organized by category.

This library contains plenty of code that relies on external programs and less
common Python libraries. The code is considered to be "extras", in the setuptools
sense. Extras can be omitted without any modification to the python code. The
following extras are supported:

  - [docx]: Support for docx file utilities requires python-docx to be
    installed.
  - [latex]: Supporting LaTeX requires a host of external programs to work
    properly, so this feature is optional. See the dependency page in the main
    documentation for more information.
  - [pdf]: Requires the poppler library to be installed.
  - [ps]: Requires GhostScript to be installed.
  - [plot]: Plotting tools require matplotlib, which is a heavy dependency, and
    unnecessary for many purposes.
  - [qt]: Some optional utilities for pyqt6 are provided if it is installed.
    Since this a heavy dependency, they are quite optional.
  - [term]: Terminal colors work out of the box on Linux, but require the
    colorama library to work on Windows.
  - [scio]: Science I/O depends on the scipy and astropy libraries to deliver
    IDL and FITS file support, respectively.
  - [xlsx]: Support for xlsx file utilities requires openpyxl to be installed.

To install extras such as latex and pdf, do:

    pip install haggis[latex,pdf]

See the documentation at <https://haggis.readthedocs.io/en/latest> for more
information, including the API documentation.

This library is licensed under the AGPLv3, and compatible with later versions.
You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
