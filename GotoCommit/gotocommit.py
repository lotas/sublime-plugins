import sublime
import sublime_plugin
import os
import subprocess
import re
import time


git_root_cache = {}
def git_root(directory):
    global git_root_cache

    retval = False
    leaf_dir = directory

    if leaf_dir in git_root_cache and git_root_cache[leaf_dir]['expires'] > time.time():
        return git_root_cache[leaf_dir]['retval']

    while directory:
        if os.path.exists(os.path.join(directory, '.git')):
            retval = directory
            break
        parent = os.path.realpath(os.path.join(directory, os.path.pardir))
        if parent == directory:
            # /.. == /
            retval = False
            break
        directory = parent

    git_root_cache[leaf_dir] = {'retval': retval, 'expires': time.time() + 5}

    return retval


class GotoCommitCommand(sublime_plugin.TextCommand):
    remote = "origin"

    def run(self, edit):
        if not self.view.file_name():
            return

        command = ['git', 'blame', '-w', '-M', '-C']

        selection = self.view.sel()[0]  # first line

        #only first line
        beginLine, beginCol = self.view.rowcol(selection.begin())

        lines = "%s,%s" % (beginLine, beginLine)
        command.extend(('-L', lines))

        gitRoot = git_root(self.view.file_name())
        os.chdir(gitRoot)
        # print "\nGit Root " + gitRoot + "\n"

        command.append(self.view.file_name())

        # print ("Executing " + ' '.join(command) + "\n")

        from subprocess import Popen, PIPE, STDOUT

        output = self.getCommandOutput(command)

        sha = re.split('\s', output)[0]

        commitUrl = self.findGithubUrl() + "commit/%s" % sha

        #inform
        sublime.status_message(commitUrl)

        self.view.window().run_command('open_url', {"url": commitUrl})

    def findGithubUrl(self):
        command = ['git', 'remote', '-v']

        remotes = self.getCommandOutput(command)

        regex = r'origin\s*(?:https://github\.com/|git@github\.com:)(.*)/(.*?)(?:\.git)'

        result = re.search(regex, remotes)
        if not result:
            sublime.status_message('Could not find origin remote')
            return ''

        matches = result.groups()

        full_link = 'https://github.com/%s/%s/' % (matches[0], matches[1])
        return full_link

    def getCommandOutput(self, command):
        from subprocess import Popen, PIPE, STDOUT

        proc = Popen(command, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        return proc.communicate()[0]
