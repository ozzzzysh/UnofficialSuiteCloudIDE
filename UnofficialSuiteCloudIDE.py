import sublime
import sublime_plugin

import os
import subprocess

import sublime_lib

# TODO Create Function for Adding Authentication to a Project

class createProjectCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		filePath = self.view.file_name();
		folderPath = os.path.dirname(os.path.abspath(filePath));

		# Prompt the user for the Project Path then prompt the user for the Project Name.
		def projectPathChosen(path):
			def projectNameChosen(projectName):
				# TODO Add indicator?
				print("Creating Project: " + projectName + " . . .");

				# Have to go to the parent directory because SuiteCloud CLI
				# creates the folder for the project in the currend directory
				os.chdir(getParentPath(path));
				# TODO Handle Errors
				try:
					returned = subprocess.check_output("suitecloud project:create --type ACCOUNTCUSTOMIZATION --projectname \"" + projectName +"\"", shell=True, universal_newlines=True);
				except:
					sublime.error_message('Error creating project. Does the project already exist?');
					return;

				print(projectName + " was successfully created.");
				def statusMessage():
					self.view.window().status_message(projectName + " was successfully created.");
				sublime.set_timeout_async(statusMessage, 1);

			# Chop off the last separator if there is one
			if path.endswith(os.sep):
				print(path[:-1]);
				path = path[:-1];

			self.view.window().show_input_panel("Project Name", os.path.basename(path), projectNameChosen, None, None);

		self.view.window().show_input_panel("Project Path (Same as the project's path in Eclipse)", folderPath, projectPathChosen, None, None);

class uploadFileCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		def everything():
			self.view.run_command('save');
			filePath = self.view.file_name();
			fileName = os.path.split(os.path.abspath(filePath))[1];
			folderPath = os.path.dirname(os.path.abspath(filePath));

			projectPath = findProjectPath(filePath);
			if projectPath == False:
				# TODO Run the Create Project Function
				sublime.error_message("Project not found.");
				return;

			os.chdir(projectPath);

			# TODO Get src directory name from suitecloud.config.js
			srcFolder = "src";
			fileCabinetFolderPath = projectPath + os.sep + srcFolder + os.sep + "FileCabinet";

			projectPathDifference = "";
			if folderPath != projectPath:
				projectPathDifference = folderPath.replace(projectPath, "")

			# TODO Add a confirmation of the folder before uploading..
			netSuiteFileCabinetPath = getNetSuiteFileCabinetPathFromReadme(projectPath);
			# Normalized to OS path separator
			fileSystemNetSuiteFileCabinetPath = netSuiteFileCabinetPath;
			# The README uses forward slashes, fix them if we're on Windows
			if os.sep == "\\":
				fileSystemNetSuiteFileCabinetPath = netSuiteFileCabinetPath.replace("/", "\\");
			if netSuiteFileCabinetPath == False:
				sublime.error_message("README not found.");
				return;

			# TODO Combine these into a function
			print("Uploading " + fileName + " . . .");
			indicator = sublime_lib.ActivityIndicator(self.view.window(), "Uploading " + fileName)
			indicator.start();

			# Copy file to the FileCabinet folder of the SDF project
			subprocess.call("xcopy \"" + filePath + "\" \"" + fileCabinetFolderPath + os.sep + fileSystemNetSuiteFileCabinetPath + projectPathDifference + os.sep + "\"", shell=True);

			# Upload the file to NetSuite
			command = "suitecloud file:upload --paths \"/" + netSuiteFileCabinetPath + projectPathDifference.replace("\\", "/") + "/" + fileName + "\"";
			success = subprocess.check_output(command, shell=True, universal_newlines=True);

			indicator.stop();

			if "The following files were uploaded:" in success:
				# TODO Combine these into a function
				print(fileName + " was successfully uploaded.");
				def statusMessage():
					self.view.window().status_message(fileName + " was successfully uploaded.");
				sublime.set_timeout_async(statusMessage, 1);
			else:
				# TODO Check for Authentication error and handle that with a new authentication function :)
				sublime.error_message(fileName + " failed to upload! Error:" + os.linesep + os.linesep + success);

			# Delete the file to keep the file system clean
			subprocess.call("del \"" + fileCabinetFolderPath + os.sep + fileSystemNetSuiteFileCabinetPath + projectPathDifference + os.sep + fileName, shell=True);

		# Kick off to another thread
		sublime.set_timeout_async(everything, 1);

def findProjectPath(filePath):
	projectFileName = "suitecloud.config.js";
	parentPath = getParentPath(filePath);

	# Find Project Directory
	projectPathToCheck = parentPath;
	# Do While Hack
	while True:
		print(projectPathToCheck);
		found = subprocess.check_output("IF EXIST \"" + projectPathToCheck + os.sep + projectFileName + "\" echo 1", shell=True, universal_newlines=True);
		if (found):
			print("Project Path Found: " + projectPathToCheck);
			return projectPathToCheck;
		else:
			if projectPathToCheck == getParentPath(projectPathToCheck):
				return False;
			else:
				projectPathToCheck = getParentPath(projectPathToCheck);

def getParentPath(path):
	return os.path.split(os.path.abspath(path))[0];

def getNetSuiteFileCabinetPathFromReadme(projectPath):
	readmeFileName = "README.txt";

	# Find Project Directory
	readmePath = projectPath;
	# Do While Hack
	while True:
		print(readmePath);
		found = subprocess.check_output("IF EXIST \"" + readmePath + os.sep + readmeFileName + "\" echo 1", shell=True, universal_newlines=True);
		if (found):
			print("README Path Found: " + readmePath);
			break;
		else:
			if readmePath == getParentPath(readmePath):
				return False;
			else:
				readmePath = getParentPath(readmePath);

	readmeFile = open(readmePath + os.sep + readmeFileName, "r");
	readmeFileLines = readmeFile.readlines();

	for line in readmeFileLines:
		if (line.startswith("SuiteScripts/")):
			print("Found NetSuite File Cabinet Path: " + line.strip());
			return line.strip();

	return False;