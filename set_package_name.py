import argparse
import os
import shutil
import string


ap = argparse.ArgumentParser()
required = ap.add_argument_group('required named arguments')
required.add_argument('-p', '--package_name',
                      required=True,
                      help="Name of package that is being create.  Python package names should be lowercase and need to be one word (no spaces).  Underscores won't break anything, but they aren't the standard.")
args = vars(ap.parse_args())

old_package_name = 'python_package_template'
new_package_name = args['package_name']
# new_package_name = 'sshauth'

## all paths are relative to the parent dir of this script
#os.chdir(os.pardir)

# exit if the package name won't work
for char in new_package_name:
    if char in string.whitespace:
        exit("Package names can't contain whitespace characters.")

# rename package directory
shutil.move(old_package_name, new_package_name)
print(f"renamed '{old_package_name}' to '{new_package_name}'")

# remove .git dir
git_dir_path = os.path.join(new_package_name, '.git')
shutil.rmtree(git_dir_path)
print(f"removed '{git_dir_path}'")

# update the config file
cfg_path = os.path.join(new_package_name, 'setup.cfg')
# cfg_path = 'python_package_template/setup.cfg'
with open(cfg_path, 'r') as f:
    old_cfg_contents = f.read().splitlines()
new_cfg_contents = []
for line in old_cfg_contents:
    if line.endswith('pkg'):
        new_line = line.replace('pkg', new_package_name)
        new_cfg_contents.append(new_line)
    else:
        new_cfg_contents.append(line)
with open(cfg_path, 'w') as f:
    f.write('\n'.join(line for line in new_cfg_contents))
print(f"updated '{cfg_path}'")

# change package dir in src
old_src_subdir_path = os.path.join(new_package_name, 'src', 'pkg')
new_src_subdir_path = os.path.join(new_package_name, 'src', new_package_name)
shutil.move(old_src_subdir_path, new_src_subdir_path)
print(f"renamed '{old_src_subdir_path}' to '{new_src_subdir_path}'")

# change package name in .gitignore
gitignore_path = os.path.join(new_package_name, '.gitignore')
# gitignore_path = 'python_package_template/.gitignore'
with open(gitignore_path, 'r') as f:
    old_gitignore_contents = f.read().splitlines()
new_gitignore_contents = []
for line in old_gitignore_contents:
    if 'pkg' in line:
        new_line = line.replace('pkg', new_package_name)
        new_gitignore_contents.append(new_line)
    else:
        new_gitignore_contents.append(line)
with open(gitignore_path, 'w') as f:
    f.write('\n'.join(line for line in new_gitignore_contents))
print(f"updated '{gitignore_path}'")

readme_path = os.path.join(new_package_name, 'README.md')
os.remove(readme_path)
print(f"removed '{readme_path}'")

print(f"""
Now you'll need to:

1. Change the values of the directives in the 'metadata' section of '{cfg_path}'.
2. Add dependency packages in the 'install_requires' directive of '{cfg_path}'.
3. Add the package's code to the '{new_src_subdir_path}' directory.
4. Upgrade pip with 'pip install -U pip' to ensure that you can install editable packages.
5. Locally install the package with 'pip install -e ./{new_package_name}'.
6. Optionally, initiate a new git repo.""")