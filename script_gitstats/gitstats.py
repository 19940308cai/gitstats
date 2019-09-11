#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import configparser
import subprocess
import datetime
import getopt
import sys


def shell(command):
    try:
        out_put = subprocess.check_output(command, shell=True)
        return out_put.decode()
    except subprocess.CalledProcessError as e:
        return None


def loadOption(config, block, option):
    try:
        return config.get(block, option)
    except Exception as e:
        return None


def conversStrToInt(str):
    try:
        return int(str)
    except Exception:
        return None


def helpCommand():
    help = '''
Command:
    -h --help 帮助命令
    -p --project 明确项目名称[默认将work_path中疑似项目列出，让用户选择]
    -s --start 统计开始时间[默认7天以前],格式[0000-00-00][7]
    -u --user 明确用户[默认所有用户]

Example:
    python gitstats.py
    python gitstats.py -p weixin -s 7
    python gitstats.py -p weixin -s 2019-01-01 -u xxxx

Config:
    work_path 表示宿主机中项目所在的父级目录,必须参数

Runtime:
    1.脚本运行时会检测当前宿主机是否有git环境
    2.脚本运行时会到work_path中去做一边基础检查,确认是否有项目存在
    3.脚本运行时会检测用户输入的project是否为合法的,合法标准为.git文件夹
'''
    sys.exit(help)


def main():
    git = shell("which git")
    if git is None:
        helpCommand()
    configer = configparser.ConfigParser()
    configer.read("./config.ini")
    workPath = loadOption(configer, "gitstats", "work_path")
    if workPath is None:
        helpCommand()
    projects = shell("ls %s" % workPath)
    if projects is None:
        helpCommand()
    else:
        projects = projects.split("\n")

    '''
    解释命令行参数
    '''
    projectName = ""
    startTime = ""
    userName = ""
    endTime = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59 +0800')
    try:
        options, args = getopt.getopt(sys.argv[1:], "h:p:s:e:u:", ["project=", "help=", "start=", "end=", "user="])
        for key, value in options:
            if key in ("-p", "--project"):
                projectName = value.strip()
            if key in ("-s", "--start"):
                startTime = value.strip()
            if key in ("-e", "--end"):
                endTime = value.strip()
            if key in ("-u", "--user"):
                userName = value.strip()
            if key in ("-h", "--help"):
                helpCommand()
    except Exception as e:
        helpCommand()

    if len(startTime) >= 11:
        helpCommand()
    # 默认开始时间是7天前
    if len(startTime) is 0:
        startTime = 7
    try:
        diff_day = int(startTime)
        startTime = (datetime.date.today() - datetime.timedelta(days=diff_day)).__str__()
    except Exception:
        pass
    finally:
        startTime += " 00:00:00 +0800"

    noProjectItems = []
    ProjectItems = []
    for project in projects:
        if project.strip() == "":
            continue
        if projectName:
            if project.strip() == projectName:
                if os.path.isdir("/".join([workPath, project])) is False:
                    helpCommand()
                else:
                    ProjectItems.append(project)
                    break
        else:
            if os.path.isdir("/".join([workPath, project])) is False:
                noProjectItems.append(project)
            else:
                ProjectItems.append(project)

    if len(ProjectItems) is 0:
        helpCommand()

    if projectName:
        projectIndex = 0
    else:
        print("请选择你要统计的项目".center(40, "-"))
        for step, project in enumerate(ProjectItems):
            step += 1
            print("".join([str(step), ":", project]))
        print("".center(50, "-"))
        try:
            while True:
                projectIndex = conversStrToInt(input(">>"))
                if projectIndex is None:
                    print("请输入正确的项目下标")
                    continue
                if projectIndex > len(ProjectItems):
                    print("请输入正确的项目下标")
                    continue
                break

        except:
            sys.exit("bye bye...")
    # 明确项目绝对路径
    projectAbsolutePath = "/".join([workPath, ProjectItems[projectIndex - 1]])

    logDate = shell("%s --git-dir=%s/.git config log.date | grep iso" % (git.strip(), projectAbsolutePath))
    if logDate is None:
        shell("%s --git-dir=%s/.git config log.date iso" % (git.strip(), projectAbsolutePath))

    if shell("ls -a %s | grep .git$" % projectAbsolutePath) is None:
        sys.exit("Error: 只能统计git项目,具体细节查看help")

    # commit author
    if userName:
        commitStr = shell(
            "%s --git-dir=%s/.git log --pretty=oneline --author=%s --pretty=format:'commit %s %s' --since='%s' --no-merges | grep commit" % (
                git.strip(), projectAbsolutePath, userName, "%H", "%aN", startTime))
    else:
        commitStr = shell(
            "%s --git-dir=%s/.git log --pretty=oneline --pretty=format:'commit %s %s' --since='%s' --no-merges | grep commit" % (
                git.strip(), projectAbsolutePath, "%H", "%aN", startTime))
    if commitStr is None:
        sys.exit('''-------------------
本次搜索commit结果为空
-------------------''')

    commitStructs = commitStr.split("\n")
    userCommits = {}
    for commit in commitStructs:
        if commit.strip() == "":
            continue
        else:
            commitArray = commit.split(" ")
            if userCommits.get(commitArray[2]) is None:
                userCommits[commitArray[2]] = [commitArray[1]]
            else:
                userCommits[commitArray[2]].append(commitArray[1])

    commitDetailTmp = "%s --git-dir=%s/.git show %s | grep '^%s\{1\}[[:space:]//[:alnum:]]' | wc -l | awk '{print $1}'"
    usersStruct = {}
    for user in userCommits:
        if usersStruct.get(user) is None:
            usersStruct[user] = {"addLine": 0, "delLine": 0, "count": 0, "commit": len(userCommits[user])}
        addStr = shell(commitDetailTmp % (git.strip(), projectAbsolutePath, " ".join(userCommits[user]), "+"))
        if addStr is not None:
            addArr = addStr.strip().split(" ")
            addlie = conversStrToInt(addArr[0])
            if addlie is not None:
                usersStruct[user]['addLine'] += addlie
        delStr = shell(commitDetailTmp % (git.strip(), projectAbsolutePath, " ".join(userCommits[user]), "-"))
        if delStr is not None:
            delArr = delStr.strip().split(" ")
            delline = conversStrToInt(delArr[0])
            if delline is not None:
                usersStruct[user]['delLine'] += delline
    report = '''-------------------
作者 %s
commit次数 %s
新增代码行数 %s
删除代码行数 %s
影响代码行数 %s 
统计日期 %s - %s
--------------------'''
    for user in usersStruct:
        print(report % (user, usersStruct[user]['commit'], usersStruct[user]['addLine'], usersStruct[user]['delLine'],
                        usersStruct[user]['addLine'] + usersStruct[user]['delLine'], startTime, endTime))


if __name__ == '__main__':
    main()
