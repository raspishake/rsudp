# rsudp doc compilation notes
### Sphinx requirements

Sphinx 2.4.4, sphinx_rtd_theme 0.4.3, and docutils 0.20.1 have to be installed in your local environment for correct compilation (`pip install -U sphinx==2.4.4`, `pip install -U docutils==0.20.1`, and `pip install -U sphinx_rtd_theme=0.4.3`).
If the current local Python version generates issues, then `Python 3.8.12` should work fine.

After installing Sphinx in your local environment, ensure that the `make.bat` and `Makefile` are present in the documentation pages folder, together with the `conf.py` file; otherwise, the `make html` action will not be executed.

For further troubleshooting:
- https://www.sphinx-doc.org/en/master/tutorial/first-steps.html#building-your-html-documentation
- https://www.sphinx-doc.org/en/master/man/sphinx-build.html

### Local compilation instructions
1. Make your edits to `.rst` files in the `_sources` folder
2. Run `make html` to compile
3. Verify that changes are acceptable in your local browser. Open the files individually from the `<buildfolder>/html` folder

### Repository compilation instructions
1. Crosscheck that the online repository files have not been updated by another user
2. Import your source file(s) modifications by simply copying/pasting in (or uploading) the modified file(s)
3. GitHub will automatically compile the new files
4. Check the results on https://raspishake.github.io/rsudp/


### DISCLAIMER

RSUDP source code and software is provided "as is". No guarantee of functionality, performance, or advertised intent is implicitly or explicitly provided.

This project is free-to-use and free-to-copy, located in the public domain, and is provided in the hope that it may be useful.

Raspberry Shake, S.A., may, from time to time, make updates to the code base, be these bug fixes or new features.  However, the company does not formally support this software / program, nor does it place itself under any obligation to respond to bug reports or new feature requests in any prescribed time frame.

Like all public projects, end-users are encouraged to provide their own bug fixes and new features as they desire: create a new branch, followed by a merge request, to have the code reviewed and folded into the main branch.

We hope you enjoy RSUDP, playing with it, and perhaps even diving into the code to see how it can be made better!

TEAM RS
