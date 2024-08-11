from main.models import Binary, GameLog, GameOutPuts, Event, EventStatus
import os
import subprocess
from subprocess import TimeoutExpired
import dotenv
from main.exceptions import TestExceptions
from pathlib import Path
from rq.timeouts import JobTimeoutException

from django.contrib.auth.models import AnonymousUser
import inspect


def log_event(request, status, features, base_id=-1):
    """
    Logs the events
    :param request:
    :param event_name: Name of the event
    :param type: Type of event
    :param status: Status of the event
    :param features: Dictionary of any features
    :return: The ID of the event
    """
    event = Event()
    event.BaseID = base_id
    try:
        event.User = request.user if not isinstance(request.user, AnonymousUser) else None
        event.Request_Type = request.method
    except:
        event.User = None
        event.Request_Type = None
    try:
        event.Name = inspect.stack()[1][3] 
        # Take notice if this ever breaks that this may be the only way to get the caller function name,
        # but it doesn't always work in production
    except:
        event.Name = '!'
    try:
        event.IP = get_client_ip(request)
    except:
        event.IP = '!'
    event.Status = status
    if not isinstance(features, str):
        event.set_features(features)
    else:
        event.Features = features
    event.save()
    return event.id


# https://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django 
# Ehtemalan Not Working, Need to fix, Apache goes COCO
def get_client_ip(request):
    """
    Gets the IP address of the request object
    :param request:
    :return:
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



if os.path.isfile(os.environ['DJ_DOTENV_PATH'] ):
    dotenv.load_dotenv(os.environ['DJ_DOTENV_PATH'] )


def kill_test_server(used_server: str):
    log_id = log_event('kill_test_server', EventStatus.COMPLETE, {'server': used_server})
    docker_script_path = os.getenv('docker_script_path')
    server_directory = os.path.join(docker_script_path, "tmp/server_directory")
    command = f'kill_server.sh -n {used_server} -sd {server_directory}'
    res1 = subprocess.run(
        f"bash {command}",
        universal_newlines=True,
        bufsize=0,
        cwd=docker_script_path,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    res2 = subprocess.run(
        f"echo 1 > {server_directory}/{used_server}",
        universal_newlines=True,
        bufsize=0,
        cwd=docker_script_path,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    log_event('kill_test_server', EventStatus.COMPLETE, {'res1_out': str(res1.stdout),
                                                         'res2_out': str(res2.stdout),
                                                         'res1_error': str(res1.stderr),
                                                         'res2_error': str(res2.stderr),
                                                         }, log_id)


def test_binary(binary_id):
    log_id = log_event('test_binary', EventStatus.STARTING, {'binary': binary_id})
    binary = Binary.objects.get(id=binary_id)
    team_name_lc = binary.team.name.lower()
    if binary.status == 'ignored':
        log_event('test_binary', EventStatus.COMPLETE, {'binary': binary_id, 'status': binary.status}, log_id)
        return
    result = subprocess.run(
        ['tar', '--warning=none', '-xvf', binary.dir_path, '--directory', os.path.join(binary.base_path, 'binary')],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    log_event('test_binary', EventStatus.IN_PROGRESS, {'tar_out': str(result.stdout), 'tar_err': str(result.stderr)}, log_id)
    if len(result.stderr) > 0:
        binary.error = f'Extract Process Error: {result.stderr.decode()}'
        binary.status = 'done_error'
        binary.done = True
        binary.save()
        log_event('test_binary', EventStatus.COMPLETE, {'error': binary.error}, log_id)
        return

    if not os.path.exists(os.path.join(binary.base_path, 'binary', binary.team.name)):
        binary.error = f'Does not follow the Structure. ' \
                       f'After extracting, the directory name should be the same as the team name.'
        binary.status = 'done_error'
        binary.done = True
        binary.save()
        log_event('test_binary', EventStatus.COMPLETE, {'error': binary.error}, log_id)
        return

    if 'start' not in os.listdir(os.path.join(binary.base_path, 'binary', binary.team.name)):
        binary.error = f'start file does not exist.'
        binary.status = 'done_error'
        binary.done = True
        binary.save()
        log_event('test_binary', EventStatus.COMPLETE, {'error': binary.error}, log_id)
        return

    binary.status = 'extracted'
    log_event('test_binary', EventStatus.IN_PROGRESS, {'status': binary.status}, log_id)
    docker_script_path = os.getenv('docker_script_path')
    test_servers_status_path = os.path.join(docker_script_path, 'tmp/server_directory')
    if not os.path.exists(test_servers_status_path):
        Path(test_servers_status_path).mkdir(parents=True, exist_ok=True)
    test_servers_status_files = os.listdir(test_servers_status_path)
    if len(test_servers_status_files) == 0:
        log_event('test_binary', EventStatus.IN_PROGRESS, 'creating servers status files', log_id)
        for i in range(1, 5):
            f = open(os.path.join(test_servers_status_path, f'test{i}'), 'w')
            f.write('1')
            f.close()
        test_servers_status_files = os.listdir(test_servers_status_path)
    free_server_count = 0
    for f in test_servers_status_files:
        file_path = os.path.join(test_servers_status_path, f)
        lines = open(file_path, 'r').readlines()
        if len(lines) == 1:
            status = int(lines[0])
            if status == 1:
                free_server_count += 1
    binary.save()
    TEST_SCRIPT_LOCATION = './run_test2.sh ' \
                           '-st "{TEST_TYPE}" ' \
                           '-sd "{TEST_SCRIPT_FOLDER}/tmp/server_directory" ' \
                           '-ld "{OUT_PUT_LOCATION}" ' \
                           '-ltbl "{LEFT_TEAM_LOCATION}" ' \
                           '-otn {ORIGINAL_TEAM_NAME} '
    command = TEST_SCRIPT_LOCATION.format(
        TEST_TYPE=binary.team.type.lower(),
        TEST_SCRIPT_FOLDER=docker_script_path,
        LEFT_TEAM_LOCATION=os.path.join(binary.base_path, 'binary', binary.team.name),
        REQUEST_ID=binary.id,
        ORIGINAL_TEAM_NAME=binary.team.name,
        OUT_PUT_LOCATION=os.path.join(binary.base_path, 'output', binary.team.name)
    )
    print('start run')
    print(command)
    binary.status = 'in_test'
    binary.save()
    try:
        if free_server_count == 0:
            raise TestExceptions(f'There is not any free server!!')
        res = subprocess.run(
            f"bash {command}",
            universal_newlines=True,
            bufsize=0,
            cwd=docker_script_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=500
        )
        binary = Binary.objects.get(id=binary_id)
        binary.std_out = str(res.stdout)
        binary.save()
        if binary.status == 'ignored':
            raise TestExceptions(
                f'You have uploaded a new binary!')
        if binary.status == 'killed':
            raise TestExceptions(
                f'The admin has killed the Game server!')
        if int(res.returncode) != 0:
            raise TestExceptions(f'error code: {res.returncode}: {res.stderr}')
        output_path = os.path.join(binary.base_path, 'output', binary.team.name)
        if not os.path.exists(output_path):
            raise TestExceptions(f'The output path is not exist:{os.path.join("output", binary.team.name)}')
        if len(os.listdir(output_path)) != 1:
            raise TestExceptions(f'The output path code is not exist:{os.path.join("output", binary.team.name)}')
        output_path_code = str(os.listdir(output_path)[0])
        output_path = os.path.join(binary.base_path, 'output', binary.team.name, output_path_code)
        game_output = GameOutPuts()
        game_output.type = 'Private'
        game_output.dir_path = output_path
        all_files = []
        exist_out_file = False
        for f in os.listdir(output_path):
            if f.endswith('out.tar.gz'):
                game_output.compressed_file_name = f
                exist_out_file = True
            if f.endswith('.log'):
                all_files.append(f)

        if len(all_files) == 0 or not exist_out_file:
            raise TestExceptions(
                f'There is no output file on the server, maybe the server has been killed,'
                f'or the game has not finished correctly!')
        game_output.set_files(all_files)
        game_output.save()
        binary.output = game_output

        game_log = GameLog()
        game_log.type = 'Private'
        game_log.dir_path = output_path
        exist_log_file = False
        exist_log_tar = False
        for f in os.listdir(output_path):
            if f.endswith('log.tar.gz'):
                game_log.compressed_file_name = f
                exist_log_tar = True
            if f.endswith('.rcg') and not f.startswith('incomplete'):
                game_log.rcg_name = f
                exist_log_file = True

        if not exist_log_file or not exist_log_tar:
            raise TestExceptions(
                f'There is no log file in the server, maybe the server has been killed, '
                f'or the game has not finished correctly!')
        game_log.save()
        rcg_path = os.path.join(game_log.dir_path, game_log.rcg_name)
        rcg_lines = open(rcg_path, 'r').readlines()[-3:]
        team_name_is_correct = False
        binary.log = game_log
        for line in rcg_lines:
            if line.find(binary.team.name) != -1:
                team_name_is_correct = True
                break
        if not team_name_is_correct:
            binary.save()
            raise TestExceptions(
                f'The start file team name is not the same as your user name ({binary.team.name}), '
                f'or the system could not run your team!')
        binary.status = 'done'
        binary.done = True
        binary.save()
        old_used_binaries_count = Binary.objects.filter(team__name=binary.team.name, use=1).count()
        team = binary.team
        team.status = True
        team.save()
        #  submit first binary
        if old_used_binaries_count == 0:
            binary_path = os.path.join(binary.base_path, 'binary', binary.team.name)
            docker_script_path = os.getenv('docker_script_path')
            docker_user_group = os.getenv('docker_user_group')

            team_name_lc = binary.team.name.lower()

            res1 = subprocess.run(
                f"rm {docker_script_path}/bins/{team_name_lc} -r",
                universal_newlines=True,
                bufsize=0,
                cwd=docker_script_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            res2 = subprocess.run(
                f"cp {binary_path} {docker_script_path}/bins/{team_name_lc} -r",
                universal_newlines=True,
                bufsize=0,
                cwd=docker_script_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            res3 = subprocess.run(
                f"chmod 777 {docker_script_path}/bins/{team_name_lc} -R",
                universal_newlines=True,
                bufsize=0,
                cwd=docker_script_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            res4 = subprocess.run(
                f"chown {docker_user_group}:{docker_user_group} {docker_script_path}/bins/{team_name_lc} -R",

                universal_newlines=True,
                bufsize=0,
                cwd=docker_script_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            log_event('test_binary', EventStatus.COMPLETE, {'submit': {'res1_out': str(res1.stdout),
                                                                       'res2_out': str(res2.stdout),
                                                                       'res3_out': str(res3.stdout),
                                                                       'res4_out': str(res4.stdout),
                                                                       'res1_err': str(res1.stderr),
                                                                       'res2_err': str(res2.stderr),
                                                                       'res3_err': str(res3.stderr),
                                                                       'res4_err': str(res4.stderr),
                                                                       }}, log_id)
            binary.use = True
            binary.save()
        print('end run')
    except Exception as e:
        import traceback
        str_error = traceback.format_exc()
        if isinstance(e, TimeoutExpired):
            str_error = 'time out!!'
        if isinstance(e, TestExceptions):
            str_error = str(e)
        if isinstance(e, JobTimeoutException):
            str_error = str(e)
        log_event('test_binary', EventStatus.ERROR, {'error': str_error, 'type': str(type(e))}, log_id)
        if binary.status != 'ignored' and binary.status != 'killed':
            binary.status = 'done-error'
        binary.error = str_error
        used_server = os.path.join(binary.base_path, 'used_server')
        if os.path.exists(used_server):
            used_server = open(used_server, 'r').readlines()[0]
            kill_test_server(used_server)
        binary.save()

def check_binary(binary_id):
    log_id = log_event('check_binary', EventStatus.STARTING, {'binary': binary_id})
    binary = Binary.objects.get(id=binary_id)
    team_name_lc = binary.team.name.lower()

    log_event('check_binary', EventStatus.IN_PROGRESS, {'status': binary.status}, log_id)
    docker_script_path = os.getenv('docker_script_path')
    test_servers_status_path = os.path.join(docker_script_path, 'tmp/server_directory')
    if not os.path.exists(test_servers_status_path):
        Path(test_servers_status_path).mkdir(parents=True, exist_ok=True)
    test_servers_status_files = os.listdir(test_servers_status_path)
    if len(test_servers_status_files) == 0:
        log_event('check_binary', EventStatus.IN_PROGRESS, 'creating servers status files', log_id)
        for i in range(1, 5):
            f = open(os.path.join(test_servers_status_path, f'test{i}'), 'w')
            f.write('1')
            f.close()
        test_servers_status_files = os.listdir(test_servers_status_path)
    free_server_count = 0
    for f in test_servers_status_files:
        file_path = os.path.join(test_servers_status_path, f)
        lines = open(file_path, 'r').readlines()
        if len(lines) == 1:
            status = int(lines[0])
            if status == 1:
                free_server_count += 1
    binary.save()
    TEST_SCRIPT_LOCATION = './run_testcheck.sh ' \
                           '-st "{TEST_TYPE}" ' \
                           '-sd "{TEST_SCRIPT_FOLDER}/tmp/server_directory" ' \
                           '-ld "{OUT_PUT_LOCATION}" ' \
                           '-ltbl "{LEFT_TEAM_LOCATION}" ' \
                           '-otn {ORIGINAL_TEAM_NAME} '
    command = TEST_SCRIPT_LOCATION.format(
        TEST_TYPE=binary.team.type.lower(),
        TEST_SCRIPT_FOLDER=docker_script_path,
        LEFT_TEAM_LOCATION=os.path.join(binary.base_path, 'binary', binary.team.name),
        REQUEST_ID=binary.id,
        ORIGINAL_TEAM_NAME=binary.team.name,
        OUT_PUT_LOCATION=os.path.join(binary.base_path, 'output', binary.team.name)
    )
    print('start runcheck')
    print(command)
    binary.status = 'in-test-check'
    binary.output = None
    binary.log = None
    binary.save()
    try:
        if free_server_count == 0:
            raise TestExceptions(f'There is not any free server!!')
        res = subprocess.run(
            f"bash {command}",
            universal_newlines=True,
            bufsize=0,
            cwd=docker_script_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=600
        )
        binary = Binary.objects.get(id=binary_id)
        binary.std_out = str(res.stdout)
        binary.save()
        if binary.status == 'killed':
            raise TestExceptions(
                f'The admin has killed the Game server!')
        if int(res.returncode) != 0:
            raise TestExceptions(f'error code: {res.returncode}: {res.stderr}')
        output_path = os.path.join(binary.base_path, 'output', binary.team.name)
        if not os.path.exists(output_path):
            raise TestExceptions(f'The output path is not exist:{os.path.join("output", binary.team.name)}')
        if len(os.listdir(output_path)) != 1:
            raise TestExceptions(f'The output path code is not exist:{os.path.join("output", binary.team.name)}')
        output_path_code = str(os.listdir(output_path)[0])
        output_path = os.path.join(binary.base_path, 'output', binary.team.name, output_path_code)
        game_output = GameOutPuts()
        game_output.type = 'Private'
        game_output.dir_path = output_path
        all_files = []
        exist_out_file = False
        for f in os.listdir(output_path):
            if f.endswith('out.tar.gz'):
                game_output.compressed_file_name = f
                exist_out_file = True
            if f.endswith('.log'):
                all_files.append(f)

        if len(all_files) == 0 or not exist_out_file:
            raise TestExceptions(
                f'There is no output file on the server, maybe the server has been killed,'
                f'or the game has not finished correctly!')
        game_output.set_files(all_files)
        game_output.save()
        binary.output = game_output

        game_log = GameLog()
        game_log.type = 'Private'
        game_log.dir_path = output_path
        exist_log_file = False
        exist_log_tar = False
        for f in os.listdir(output_path):
            if f.endswith('log.tar.gz'):
                game_log.compressed_file_name = f
                exist_log_tar = True
            if f.endswith('.rcg') and not f.startswith('incomplete'):
                game_log.rcg_name = f
                exist_log_file = True

        if not exist_log_file or not exist_log_tar:
            raise TestExceptions(
                f'There is no log file in the server, maybe the server has been killed, '
                f'or the game has not finished correctly!')
        game_log.save()
        rcg_path = os.path.join(game_log.dir_path, game_log.rcg_name)
        rcg_lines = open(rcg_path, 'r').readlines()[-3:]
        team_name_is_correct = False
        binary.log = game_log
        for line in rcg_lines:
            if line.find(binary.team.name) != -1:
                team_name_is_correct = True
                break
        if not team_name_is_correct:
            binary.save()
            raise TestExceptions(
                f'The start file team name is not the same as your user name ({binary.team.name}), '
                f'or the system could not run your team!')
        binary.status = 'done-checked'
        binary.done = True
        binary.save()
        old_used_binaries_count = Binary.objects.filter(team__name=binary.team.name, use=1).count()
        team = binary.team
        team.status = True
        team.save()
        binary.save()
        print('end runcheck')
    except Exception as e:
        import traceback
        str_error = traceback.format_exc()
        if isinstance(e, TimeoutExpired):
            str_error = 'time out!!'
        if isinstance(e, TestExceptions):
            str_error = str(e)
        if isinstance(e, JobTimeoutException):
            str_error = str(e)
        log_event('check_binary', EventStatus.ERROR, {'error': str_error, 'type': str(type(e))}, log_id)
        if binary.status != 'ignored' and binary.status != 'killed':
            binary.status = 'done-checked-error'
        binary.error = str_error
        used_server = os.path.join(binary.base_path, 'used_server')
        if os.path.exists(used_server):
            used_server = open(used_server, 'r').readlines()[0]
            kill_test_server(used_server)
        binary.save()