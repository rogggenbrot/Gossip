from distutils.core import setup

#This is a list of files to install, and where
#(relative to the 'root' dir, where setup.py is)
#You could be more specific.
files = ["*"]

setup(name = "gossip",
    version = "0.0.1",
    description = "Gossiping Open Source Service Interface Police",
    author = "Patrick Rockenschaub",
    author_email = "rogggenbrot@gmail.com",
    url = "www.2point0.at",
    #Name the folder where your packages live:
    #(If you have other packages (dirs) or modules (py files) then
    #put them into the package directory - they will be found 
    #recursively.)
    packages = ['gossip'],
    #'package' package must contain files (see list above)
    #I called the package 'package' thus cleverly confusing the whole issue...
    #This dict maps the package name =to=> directories
    #It says, package *needs* these files.
    package_data = {'gossip' : files },
    #'runner' is in the root.
    scripts = ["application.py"],
    #install_path = '~/gossip',
    long_description = """Gossip library provides the infrastructure to build a peer to peer network in order to supervise proclaimed services from multiple network locations to minimize false alarms.""" 
    #
    #This next part is for the Cheese Shop, look a little down the page.
    #classifiers = []     
) 