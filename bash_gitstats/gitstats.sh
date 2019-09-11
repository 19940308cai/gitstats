#!/bin/bash

source ./conf.sh

if [ ${#base_path} == 0 ]; then
    base_path="./"
fi

git=`which git`
if [ ${#git} == 0 ]; then
    echo -e "\033[31mplease install git programing\033[0m"
    exit
fi

projects=`ls ${base_path}`

if [ ${#projects} == 0 ]; then
    echo -e "\033[31not project in ${base_path}\033[0m"
    exit
fi

key=0
echo -e "\033[36m------------------
请选择需要统计的项目:\033[0m"
for project in ${projects[@]}; do
    key=`expr ${key} + 1`
    echo -e "\033[36m索引:${key} 项目名称:${project}\033[0m"
done
echo -e "\033[36m------------------\033[0m"

read select

index=`expr ${select} - 1`

projects=(${projects})

cd ${base_path}/${projects[$index]}

isGitWorkPath=`ls -a | grep '\.git'`
if [ ${#isGitWorkPath} == 0 ]; then
    echo -e "\033[31mscript need run in git work path\033[0m"
    exit
fi

echo -e "\033[36m
------------------
Parameter Format:
1.author - git用户名
2.since  - 北京时间(2019-01-01 00:00:00)

Explain:
1.author为空时默认取本机用户
2.since表示数据区间的开始时间
------------------
\033[0m"

echo -e "\033[32m请输入用户名称\033[0m"
read author
echo -e "\033[32m请输入时间\033[0m"
read since

if [ ${#author} == 0 ]; then
    author=`${git} config user.name`
fi

if [ ${#since} == 0 ]; then
    since=`date -v-7d "+%Y-%m-%d 00:00:00 +0800"`
elif [ ${#since} -le 4 ]; then
    since=`date -v-${since}d "+%Y-%m-%d 00:00:00 +0800"`
else
    since=${since}+" +0800"
fi

`${git} config log.date iso`

author_commits=`${git} log --author="${author}" --since="${since}" --no-merges | grep commit`

zero_commit=0
if [ ${#author_commits} == 0 ]; then
    zero_commit=1
fi

if [ ${zero_commit} == 1 ]; then
echo -e "\033[36m------------------
作者:${author}
时间区间:[${since} - `date "+%Y-%m-%d %H:%M:%S"`]
添加总行数:0
删除总行数:0
受影响函数:0
说明:用户在该时间区间段内没有commit提交
------------------\033[0m"
else
        count_line=0
        delete_count_line=0
        commits=($author_commits)
        for value in ${commits[@]}; do
                if [ ${value} != "commit" ]; then
                    commit_line=`${git} show ${value} | grep "^+\{1\}[[:space:]//[:alnum:]]" | wc -l | awk '{print $1}'`
                    count_line=`expr ${count_line} + ${commit_line}`
                    delete_commit_line=`${git} show ${value} | grep "^-\{1\}[[:space:]//[:alnum:]]" | wc -l | awk '{print $1}'`
                    delete_count_line=`expr ${delete_count_line} + ${delete_commit_line}`
echo "------------------
commit ID: ${value}
add line length: ${commit_line}
delete line length: ${delete_count_line}
------------------
"
                fi
        done
echo -e "\033[36m------------------
作者:${author}
时间区间:[${since} - `date "+%Y-%m-%d %H:%M:%S"`]
添加总行数:${count_line}
删除总行数:${delete_count_line}
受影响行数:`expr ${count_line} + ${delete_count_line}`
------------------\033[0m
"
fi
