from asyncio import events
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from main.models import Iframe, Team, Binary, BinaryStatus, UploadStatus, LongTestStatus, EventStatus, Event
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
import traceback
from main.forms import TeamForm, DocumentForm, IframeForm
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.storage import default_storage
import django_rq
from rq.job import Job
from main.utils import test_binary, check_binary, kill_test_server, log_event
import mimetypes
import os
import csv
from django.utils.timezone import now
import django
import dotenv
import subprocess
from django.contrib.auth.decorators import user_passes_test
from pathlib import Path
from django.core.mail import send_mail
from django.conf import settings

def error_400(request, *args, **argv):
    return render(request, '403.html', status=400)

def error_403(request, *args, **argv):
    return render(request, '403.html', status=403)

def error_404(request, *args, **argv):
    return render(request, '404.html', status=404)


def error_500(request, *args, **argv):
    return render(request, '500.html', status=500)


if os.path.isfile(os.environ['DJ_DOTENV_PATH'] ):
    dotenv.load_dotenv(os.environ['DJ_DOTENV_PATH'] )


def get_home_iframe(request):
    iframes = Iframe.objects.all()
    return render(request, 'home.html', {'iframes': iframes})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def get_teams_view(request):
    log_id = log_event(request, EventStatus.STARTING, '')
    teams = Team.objects.all()
    log_event(request, EventStatus.COMPLETE, {'teams': [t.name for t in teams]}, log_id)
    return render(request, template_name='teams.html', context={'teams': teams})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_team_view(request):
    log_id = log_event(request, EventStatus.STARTING, '')
    teams = Team.objects.all()
    if request.method == 'GET':
        form = TeamForm()
    else:
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save()
            user = User.objects.create_user(username=team.name,
                                            email=team.email,
                                            password=team.password)
            user.save()
            team.user = user
            team.save()
            log_event(request, EventStatus.COMPLETE, {'user': user.username, 'email': user.email}, log_id)
            log_id = log_event(request, EventStatus.STARTING, {'email': user.email, 'user': user.username}, log_id)
            site_name = 'https://rcss.dev/'
            message = f'''Dear {team.name} Team ,

            Welcome to RoboCup 20XX Soccer Simulation 2D Tournament Manager

            You can find the log in at: 
                    {site_name}
            Your Team username is: 
                    {user.username}
            Your Team password is: 
                    {team.password}

            please check the information board and rules for this year of Competition.
            https://docs.google.com/

            Do not hesitate to ask if you have any Questions or Concerns
            Official discord server for RCSS2D:
            https://discord.gg/MJgXsaEguX

Best Regards,
SS2DTMR
RoboCup20XX Committee
            '''
            subject = "Welcome to SS2DTM | Your Team is Ready"
            email_from = settings.DEFAULT_FROM_EMAIL
            recipient_list = [team.email] 

            if recipient_list:
                try:
                    send_mail(subject,message,email_from,recipient_list)
                    # send_mail(subject,html_message=message,from_email=email_from,recipient_list=recipient_list)

                except Exception as e:
                    str_error = traceback.format_exc()
                    log_event(request, EventStatus.ERROR, {'error': str_error}, log_id)

        else:
            messages.error(request, form.errors)
            #  TODO add error to event
            log_event(request, EventStatus.ERROR, {'error': str(form.errors.as_json())}, log_id)
            return render(request, template_name='teams.html', context={'teams': teams , 'team_form': form.cleaned_data})

    return render(request, template_name='teams.html', context={'teams': teams , 'team_form': form.cleaned_data})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_team(request,id):
    log_id = log_event(request, EventStatus.STARTING, '')
    try:
        team = Team.objects.get(pk=id)
        if request.method == 'GET':
            form = TeamForm(instance=Team(team))
            log_event(request, EventStatus.COMPLETE, {'team': team.name}, log_id)
            return render(request, template_name='edit_team.html', context={'team':team, 'team_form': form})
        else:
            form = TeamForm(request.POST, instance=team)
            if form.is_valid():
                tform = form.save(commit=False)
                team.user.username=tform.name
                team.user.set_password(tform.password)
                team.user.email=tform.email
                team.user.save()
                # tform.user=team.user
                # tform.user.save()
                tform.save()
                log_event(request, EventStatus.COMPLETE, {'team': team.name}, log_id)
            else:
                messages.error(request, form.errors)
                log_event(request, EventStatus.ERROR, {'error': form.errors.as_json()}, log_id)
                return render(request, template_name='edit_team.html', context={'team':team, 'team_form': form.data})

        return redirect('get_teams_view')
    except Exception as e:
        str_error = traceback.format_exc()
        log_event(request, EventStatus.ERROR, {'error': str_error}, log_id)
        return redirect('get_teams_view')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def del_team(request,id):
    log_id = log_event(request, EventStatus.STARTING, '')
    try:
        team = Team.objects.get(id=id)
        binaries = Binary.objects.filter(team=team)
        if binaries:
            binaries.delete()
        if team.user:
            team.user.delete()
        team.delete()
        log_event(request, EventStatus.COMPLETE, {'team': team.name}, log_id)
    except Exception as e:
        str_error = traceback.format_exc()
        log_event(request, EventStatus.ERROR, {'error': str_error}, log_id)
    return redirect('get_teams_view')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def csv_teams_export(request):
    log_id = log_event(request, EventStatus.STARTING, '')
    teams = Team.objects.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="csv_teams_export_{django.utils.timezone.now()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['user_name', 'password', 'team_name_lc', 'email', 'last_upload', 'status'])

    for team in teams:
        writer.writerow([team.name, team.password ,team.name.lower(), team.type.lower(), team.email,team.last_upload, team.status])
    log_event(request, EventStatus.COMPLETE, {'teams': [t.name for t in teams]}, log_id)
    return response

@login_required  
@user_passes_test(lambda u: u.is_superuser)
def add_iframe(request):
    if request.method == 'GET':
        form = IframeForm()
    else:
        form = IframeForm(request.POST)
        if form.is_valid():
            iframe = form.save()
        else:
            messages.error(request, form.errors)
            upload_status = can_team_upload()
            long_test_status = can_team_long_test()
            iframes = Iframe.objects.all()
            test_servers_status = []
            docker_script_path = os.getenv('docker_script_path')
            docker_status = Path(os.path.join(docker_script_path,'.env')).is_file()
            test_servers_status_path = os.path.join(
                docker_script_path, 'tmp/server_directory')
            if not docker_status:
                return render(request, 'control_panel.html', {'upload_status': upload_status, 'long_test_status':long_test_status,'iframes': iframes,
                                                        'test_servers_status': test_servers_status,
                                                        'docker_status': docker_status})
            if not os.path.exists(test_servers_status_path):
                Path(test_servers_status_path).mkdir(
                    parents=True, exist_ok=True)
            test_servers_status_files = os.listdir(test_servers_status_path)
            if len(test_servers_status_files) == 0:
                for i in range(1, 5):
                    f = open(os.path.join(
                        test_servers_status_path, f'test{i}'), 'w')
                    f.write('1')
                    f.close()
                test_servers_status_files = os.listdir(
                    test_servers_status_path)
            for f in test_servers_status_files:
                file_path = os.path.join(test_servers_status_path, f)
                lines = open(file_path, 'r').readlines()
                if len(lines) != 1:
                    test_servers_status.append([f, 'Error'])
                else:
                    status = int(lines[0])
                    if status == 1:
                        test_servers_status.append([f, 'Free'])
                    else:
                        test_servers_status.append([f, 'InUsed'])
            return render(request, 'control_panel.html', {'iframe_form': form.cleaned_data, 'upload_status': upload_status,'long_test_status':long_test_status,
                                                           'iframes': iframes,'test_servers_status': test_servers_status,'docker_status':docker_status})

        return redirect('control_panel')

    return render(request, 'control_panel.html', {'iframe_form': form})

@login_required  
@user_passes_test(lambda u: u.is_superuser)
def init_dtr(request):
    log_id = log_event(request, EventStatus.STARTING, '')
    try:
        docker_script_path = os.getenv('docker_script_path')
        docker_status = Path(os.path.join(docker_script_path,'.env')).is_file()
        docker_user_group = os.getenv('docker_user_group')

        if not docker_status:
            if os.path.exists(docker_script_path):
                res = subprocess.run(
                    f"rm -rf {docker_script_path}",
                    universal_newlines=True,
                    bufsize=0,
                    cwd=docker_script_path,
                    shell=True
                )
            if not os.path.exists(Path(docker_script_path).parent):
                Path(Path(docker_script_path).parent).mkdir(parents=True, exist_ok=True)
            try:
                res1 = subprocess.run(
                    f"chown :{docker_user_group} .",
                    universal_newlines=True,
                    bufsize=0,
                    cwd=Path(docker_script_path).parent,
                    shell=True
                )
                from git import Repo
                Repo.clone_from("https://github.com/RCSS-IR/SS2D-Docker-Tournament-Runner.git", docker_script_path)
                res2 = subprocess.run(
                    f"cp .env.example .env",
                    universal_newlines=True,
                    bufsize=0,
                    cwd=docker_script_path,
                    shell=True
                )
                res3 = subprocess.run(
                    f"chown :{docker_user_group} {docker_script_path} -R",
                    universal_newlines=True,
                    bufsize=0,
                    cwd=docker_script_path,
                    shell=True
                )
                res4 = subprocess.run(
                    f"chmod 777 {docker_script_path} -R",
                    universal_newlines=True,
                    bufsize=0,
                    cwd=docker_script_path,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                # mkdir -p ./bins/agent/bin &&  tar -xf ./test_bins/agent.tar.gz -C ./bins/agent/bin
                # mv ./bins/agent/bin/agent/* ./bins/agent/bin/
                # no test bin (add local)
                res5 = subprocess.run(
                    f"./build_all.sh",
                    universal_newlines=True,
                    bufsize=0,
                    cwd=docker_script_path,
                    shell=True
                )

                log_event(request, EventStatus.COMPLETE, {'git_init_dtr': {'res1_out': str(res1.stdout),
                                                                'res2_out': str(res2.stdout),
                                                                'res3_out': str(res3.stdout),
                                                                'res4_out': str(res4.stdout),
                                                                'res5_out': str(res5.stdout),
                                                                'res1_err': str(res1.stderr),
                                                                'res2_err': str(res2.stderr),
                                                                'res3_err': str(res3.stderr),
                                                                'res4_err': str(res4.stderr),
                                                                'res5_err': str(res5.stderr),
                                                                }}, log_id)
            except:
                return redirect('control_panel')
    except:
        return redirect('control_panel')
    return redirect('control_panel')


@login_required         
@user_passes_test(lambda u: u.is_superuser)
def del_iframe(request,id):
    Iframe.objects.get(id=id).delete()
    return redirect('control_panel')

def can_team_upload():
    upload_status = False
    if UploadStatus.objects.all().count() != 0:
        upload_status = UploadStatus.objects.all().order_by('-change_date')[0].status
    return upload_status

def can_team_long_test():
    long_test_status = False
    if LongTestStatus.objects.all().count() != 0:
        long_test_status = LongTestStatus.objects.all().order_by('-change_date')[0].status
    return long_test_status

@login_required
def upload_team_view(request):
    log_id = log_event(request, EventStatus.STARTING, '')
    try:
        is_admin = False
        team = None
        if request.user.is_superuser:
            is_admin = True
        else:
            team = Team.objects.get(name=request.user.username)
        upload_status = can_team_upload()
        long_test_status = can_team_long_test()
        if (is_admin or upload_status) and request.method == 'POST':
            form = DocumentForm(request.POST, request.FILES)
            is_valid = form.is_valid()
            file_name: InMemoryUploadedFile | None = None
            team_name = None
            if is_valid:
                file_name = request.FILES['file']
                if is_admin:
                    team_name = str(file_name).split('.')[0]
                    if team_name not in list(Team.objects.all().values_list('name', flat=True)):
                        form.add_error('file', f'Wrong Name: No team has been registered with this name ({team_name})!')
                        is_valid = False
                    if is_valid:
                        team = Team.objects.get(name=team_name)
                    else:
                        log_event(request, EventStatus.ERROR, {'error': form.errors.as_text()}, log_id)
                        return JsonResponse({'data':form.errors.as_text()})

                elif team:
                    team_name = team.name
                log_event(request, EventStatus.IN_PROGRESS, {'team': str(team_name), 'file': str(file_name)}, log_id)
            if is_valid:
                accepted_file_type = ['application/x-compressed-tar',
                                      'application/x-xz-compressed-tar',
                                      'application/x-xz',
                                      'application/gzip',
                                      'application/x-gzip']
                if str(file_name).split('.')[0] != team_name:
                    form.add_error('file', f'The uploaded file name ({file_name}) should be the same as the team name!')
                    is_valid = False
                elif not str(file_name).endswith('.tar.gz') and not str(file_name).endswith('.tar.xz'):
                    form.add_error('file', 'The Uploaded File Extension should be tar.gz or tar.xz!')
                    is_valid = False
                elif file_name.content_type not in accepted_file_type:
                    form.add_error('file', f'The type of Uploaded file ({file_name.content_type}) should be {accepted_file_type}!')
                    is_valid = False
                elif file_name.size > 214958080:  # 250MB:
                    form.add_error('file', 'The uploaded file size can not exceed 250MB.')
                    is_valid = False

            if not is_valid:
                log_event(request, EventStatus.ERROR, {'error': form.errors.as_text()}, log_id)
                return JsonResponse({'data': form.errors.as_text()})

            if is_valid:
                old_binaries = Binary.objects.filter(team=Team.objects.get(name=team_name))
                binary = Binary()
                binary.save()
                log_event(request, EventStatus.IN_PROGRESS, {'team': team_name, 'binary': binary.id}, log_id)
                for old_binary in old_binaries:
                    if old_binary.status in ['saved', 'extracted', 'in_queue']:
                        log_event(request, EventStatus.IN_PROGRESS, {'team': team_name, 'binary': binary.id,
                                                                     'old_binary': old_binary.id,
                                                                     'old_status': old_binary.status,
                                                                     'old_new_status': 'ignored'}, log_id)
                        old_binary.status = 'ignored'
                        old_binary.save()
                    if old_binary.status in ['in_test']:
                        log_event(request, EventStatus.IN_PROGRESS, {'team': team_name, 'binary': binary.id,
                                                                     'old_binary': old_binary.id,
                                                                     'old_status': old_binary.status,
                                                                     'old_new_status': 'ignored'}, log_id)
                        old_binary.status = 'ignored'
                        used_server = os.path.join(old_binary.base_path, 'used_server')
                        if os.path.exists(used_server):
                            used_server = open(used_server, 'r').readlines()[0]
                            log_event(request, EventStatus.IN_PROGRESS, {'team': team_name, 'binary': binary.id,
                                                                         'server_file': used_server,
                                                                         'used_server': used_server}, log_id)
                            kill_test_server(used_server)
                        old_binary.save()
                django_path = os.environ['DJ_BASE_DIR']
                save_path = os.path.join(django_path, f'upload/{team_name}/{binary.id}/binary/{file_name}')
                file_name = default_storage.save(save_path, request.FILES['file'])
                binary.team = team
                binary.file_name = file_name
                binary.dir_path = save_path
                binary.status = 'saved'
                binary.base_path = os.path.join(django_path, f'upload/{team_name}/{binary.id}')
                binary.done = False
                binary.save()
                team.last_upload = django.utils.timezone.now()
                team.save()
                queue = django_rq.get_queue('default')
                job: Job = queue.enqueue(test_binary, args=(binary.id,))
                log_event(request, EventStatus.IN_PROGRESS, {'team': team_name, 'binary': binary.id,
                                                             'status': binary.status,
                                                             'path': binary.dir_path,
                                                             'job': job.id}, log_id)
                return JsonResponse({'data':'Data uploaded'})

            else:
                log_event(request, EventStatus.ERROR, {'error': form.errors.as_text()}, log_id)
                return JsonResponse({'data':form.errors.as_text()})

        #         https://github.com/rq/django-rq
        else:
            log_event(request, EventStatus.IN_PROGRESS, {'admin': is_admin, 'upload_status': upload_status,'long_test_status':long_test_status}, log_id)
            form = DocumentForm()

        bins = []
        for binary in Binary.objects.all().order_by('-start_date'):
            if is_admin:
                bins.append(binary)
            elif team and binary.team == team:
                bins.append(binary)
        log_event(request, EventStatus.COMPLETE, {}, log_id)
        return render(request, template_name='team_upload.html', context={'binaries': bins,
                                                                          'form': form,
                                                                          'upload_status': upload_status,
                                                                          'long_test_status':long_test_status})
    except Exception as e:
        str_error = traceback.format_exc()
        log_event(request, EventStatus.ERROR, {'error': str_error}, log_id)
        return JsonResponse({'data':str_error})
        # return error_500(request) 

@login_required
def download_log(request, id):
    log_id = log_event(request, EventStatus.STARTING, '')
    is_admin = False
    is_team = False
    team_name = ''
    if request.user.is_superuser:
        is_admin = True
    else:
        team_name = Binary.objects.get(id=id).team.name
        if request.user.username == team_name:
            is_team = True
    log_event(request, EventStatus.IN_PROGRESS, {'is_admin': is_admin, 'is_team': is_team,
                                                 'team_name': team_name}, log_id)
    if is_team or is_admin:
        binary = Binary.objects.get(id=id)
        file_path = os.path.join(binary.log.dir_path, binary.log.compressed_file_name)
        path = open(file_path, 'rb')
        mime_type, _ = mimetypes.guess_type(file_path)
        response = HttpResponse(path, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % binary.log.compressed_file_name
        log_event(request, EventStatus.COMPLETE, {'binary': binary.id}, log_id)
        return response
    else:
        log_event(request, EventStatus.ERROR, '', log_id)
        return redirect('/')


@login_required
def download_out(request, id):
    log_id = log_event(request, EventStatus.STARTING, '')
    is_admin = False
    is_team = False
    team_name = ''
    if request.user.is_superuser:
        is_admin = True
    else:
        team_name = Binary.objects.get(id=id).team.name
        if request.user.username == team_name:
            is_team = True
    log_event(request, EventStatus.IN_PROGRESS, {'is_admin': is_admin, 'is_team': is_team,
                                                 'team_name': team_name}, log_id)
    if is_team or is_admin:
        binary = Binary.objects.get(id=id)
        file_path = os.path.join(binary.output.dir_path, binary.output.compressed_file_name)
        path = open(file_path, 'rb')
        mime_type, _ = mimetypes.guess_type(file_path)
        response = HttpResponse(path, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % binary.output.compressed_file_name
        log_event(request, EventStatus.COMPLETE, {'binary': binary.id}, log_id)
        return response
    else:
        log_event(request, EventStatus.ERROR, '', log_id)
        return redirect('/')


@login_required
def download_binary(request, id):
    log_id = log_event(request, EventStatus.STARTING, '')
    is_admin = False
    is_team = False
    team_name = ''
    if request.user.is_superuser:
        is_admin = True
    else:
        team_name = Binary.objects.get(id=id).team.name
        if request.user.username == team_name:
            is_team = True
    log_event(request, EventStatus.IN_PROGRESS, {'is_admin': is_admin, 'is_team': is_team,
                                                 'team_name': team_name}, log_id)
    if is_team or is_admin:
        binary = Binary.objects.get(id=id)
        file_path = binary.dir_path
        if os.path.exists(file_path):
            path = open(file_path, 'rb')
            mime_type, _ = mimetypes.guess_type(file_path)
            response = HttpResponse(path, content_type=mime_type)
            response['Content-Disposition'] = "attachment; filename=%s" % binary.file_name.split('/')[-1]
            log_event(request, EventStatus.COMPLETE, {'binary': binary.id}, log_id)
            return response
        else:
            log_event(request, EventStatus.ERROR, '', log_id)
            return redirect('/main/upload_page')
    else:
        log_event(request, EventStatus.ERROR, '', log_id)
        return redirect('/')


@login_required
def submit_bin(request, id):
    log_id = log_event(request, EventStatus.STARTING, '')
    is_admin = False
    is_team = False
    team_name = ''
    if request.user.is_superuser:
        is_admin = True
    else:
        team_name = Binary.objects.get(id=id).team.name
        if request.user.username == team_name:
            is_team = True
    log_event(request, EventStatus.IN_PROGRESS, {'is_admin': is_admin, 'is_team': is_team,
                                                 'team_name': team_name}, log_id)
    if is_admin or (is_team and can_team_upload()):
        binary = Binary.objects.get(id=id)
        if binary.status != 'done' and binary.status != 'done-checked':
            log_event(request, EventStatus.ERROR, {'binary_status': binary.status}, log_id)
            return redirect('/main/upload_page')
        old_binaries = Binary.objects.filter(team__name=binary.team.name)
        for old_binary in old_binaries:
            old_binary.use = False
            log_event(request, EventStatus.IN_PROGRESS, {'old_binary': old_binary.id}, log_id)
            old_binary.save()
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
            timeout=500
        )
        res2 = subprocess.run(
            f"cp {binary_path} {docker_script_path}/bins/{team_name_lc} -r",
            universal_newlines=True,
            bufsize=0,
            cwd=docker_script_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=500
        )
        res3 = subprocess.run(
            f"chmod 777 {docker_script_path}/bins/{team_name_lc} -R",
            universal_newlines=True,
            bufsize=0,
            cwd=docker_script_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=500
        )
        res4 = subprocess.run(
            f"chown {docker_user_group}:{docker_user_group} {docker_script_path}/bins/{team_name_lc} -R",
            universal_newlines=True,
            bufsize=0,
            cwd=docker_script_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=500
        )
        binary.use = True
        binary.save()
        log_event(request, EventStatus.COMPLETE, {'binary': binary.id,
                                                  'res1_out': str(res1.stdout),
                                                  'res2_out': str(res2.stdout),
                                                  'res3_out': str(res3.stdout),
                                                  'res4_out': str(res4.stdout),
                                                  'res1_err': str(res1.stderr),
                                                  'res2_err': str(res2.stderr),
                                                  'res3_err': str(res3.stderr),
                                                  'res4_err': str(res4.stderr)
                                                  }, log_id)
        return redirect('/main/upload_page')
    else:
        return redirect('/main/upload_page')

@login_required
def check_bin(request, id):
    log_id = log_event(request, EventStatus.STARTING, '')
    is_admin = False
    is_team = False
    team_name = ''
    if request.user.is_superuser:
        is_admin = True
    else:
        team_name = Binary.objects.get(id=id).team.name
        if request.user.username == team_name:
            is_team = True
    log_event(request, EventStatus.IN_PROGRESS, {'is_admin': is_admin, 'is_team': is_team,
                                                 'team_name': team_name}, log_id)
    if is_admin or (is_team and can_team_upload()):
        binary = Binary.objects.get(id=id)
        if binary.status != 'done':
            log_event(request, EventStatus.ERROR, {'binary_status': binary.status}, log_id)
            return redirect('/main/upload_page')
        old_binaries = Binary.objects.filter(team__name=binary.team.name)
        for old_binary in old_binaries:
            old_binary.use = False
            log_event(request, EventStatus.IN_PROGRESS, {'old_binary': old_binary.id}, log_id)
            old_binary.save()
        binary_path = os.path.join(binary.base_path, 'binary', binary.team.name)
        docker_script_path = os.getenv('docker_script_path')
        docker_user_group = os.getenv('docker_user_group')

        team_name_lc = binary.team.name.lower()
        queue = django_rq.get_queue('default')
        job: Job = queue.enqueue(check_binary, args=(binary.id,))
        log_event(request, EventStatus.IN_PROGRESS, {'team': team_name, 'binary': binary.id,
                                                        'status': binary.status,
                                                        'path': binary.dir_path,
                                                        'job': job.id}, log_id)
        
        binary.use = True
        binary.status = 'in-test-check'

        binary.save()

        return redirect('/main/upload_page')
    else:
        return redirect('/main/upload_page')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def control_panel(request):
    log_id = log_event(request, EventStatus.STARTING, '')
    upload_status = can_team_upload()
    long_test_status = can_team_long_test()
    iframes = Iframe.objects.all()
    test_servers_status = []
    test_servers_names = []
    bn_team_in_test = Binary.objects.filter(status='in_test') | Binary.objects.filter(status='in-test-check')
    docker_script_path = os.getenv('docker_script_path')
    if docker_script_path == '' or docker_script_path is None: 
        django_path = os.environ['DJ_BASE_DIR']
        messages.error(request, f'The Docker Script not Dectected, please check .env file at {django_path}/SS2DTournamentRunner')
        return render(request, 'control_panel.html', {'upload_status': upload_status,'long_test_status':long_test_status,
                                                'iframes': iframes,'test_servers_status': test_servers_status,
                                                'docker_status': True})

    docker_status = Path(os.path.join(docker_script_path,'.env')).is_file()
    test_servers_status_path = os.path.join(docker_script_path, 'tmp/server_directory')
    if not docker_status:
        messages.error(request, f'The Docker Script location is set at {docker_script_path}, \
                       please download the script form the git directory or use the init button')
        return render(request, 'control_panel.html', {'upload_status': upload_status,'long_test_status':long_test_status, 'iframes': iframes,
                                                'test_servers_status': test_servers_status, 'test_servers_names': test_servers_names,
                                                'docker_status': docker_status})
    try:
        if not os.path.exists(test_servers_status_path):
            Path(test_servers_status_path).mkdir(parents=True, exist_ok=True)
        test_servers_status_files = os.listdir(test_servers_status_path)
        if len(test_servers_status_files) == 0:
            log_event(request, EventStatus.IN_PROGRESS, 'Creating server status files', log_id)
            for i in range(1, 5):
                f = open(os.path.join(test_servers_status_path, f'test{i}'), 'w')
                f.write('1')
                f.close()
            test_servers_status_files = os.listdir(test_servers_status_path)
            log_event(request, EventStatus.IN_PROGRESS, 'Created server status files', log_id)
        log_event(request, EventStatus.IN_PROGRESS, 'Find server status files for binaries', log_id)
        for bn in bn_team_in_test:
            used_server = os.path.join(bn.base_path, 'used_server')
            if os.path.exists(used_server):
                used_server = open(used_server, 'r').readlines()[0]
            test_servers_names.append([used_server, bn.team.name])
        for f in test_servers_status_files:
            file_path = os.path.join(test_servers_status_path, f)
            lines = open(file_path, 'r').readlines()
            team_is_not_in = True
            if len(lines) != 1:
                for team in test_servers_names:
                    if team[0] == f:
                        team_is_not_in = False
                    test_servers_status.append([f, team[1], 'Error'])

                if team_is_not_in:
                    test_servers_status.append([f, 'None', 'Error'])
            else:
                status = int(lines[0])
                if status == 1:
                    test_servers_status.append([f, 'None', 'Free'])
                else:
                    for team in test_servers_names:
                        if f == team[0].strip():
                            team_is_not_in = False
                            test_servers_status.append([f, team[1], 'InUsed'])

                    if team_is_not_in:
                        test_servers_status.append([f, 'None', 'InUsed'])
            log_event(request, EventStatus.COMPLETE, {'test_servers_status': test_servers_status}, log_id)
        return render(request, 'control_panel.html', {'upload_status': upload_status,'long_test_status':long_test_status, 'iframes':iframes,
                                                      'test_servers_status': test_servers_status , 'test_servers_names':test_servers_names,
                                                      'docker_status': docker_status})
    except Exception as e:
        str_error = traceback.format_exc()
        log_event(request, EventStatus.FATAL, {'error': str_error}, log_id)
        return error_500(request)

    
@login_required
@user_passes_test(lambda u: u.is_superuser)
def kill_server(request, server_id):
    log_id = log_event(request, EventStatus.STARTING, {'server_id': server_id})
    in_test_bins = Binary.objects.filter(status='in_test')
    for bin in in_test_bins:
        if bin.status in ['in_test']:
            used_server = os.path.join(bin.base_path, 'used_server')
            if os.path.exists(used_server):
                used_server = open(used_server, 'r').readlines()[0]
                if used_server.strip() == server_id.strip():
                    bin.status = 'killed'
                    kill_test_server(used_server)
                    bin.save()
                    log_event(request, EventStatus.STARTING, {'binary': bin.id, 'team': bin.team.name}, log_id)
                    return redirect('control_panel')
    kill_test_server(server_id)
    log_event(request, EventStatus.COMPLETE, '', log_id)
    return redirect('control_panel')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def change_upload_status(request):
    log_id = log_event(request, EventStatus.STARTING, '')
    if request.method == 'POST':
        if UploadStatus.objects.all().count() == 0:
            upload_status = UploadStatus()
        else:
            upload_status = UploadStatus.objects.all().order_by('-change_date')[0]
        upload_status.status = request.POST.get('upload_status') == 'true'
        if upload_status.status:
            message = '''Dear Team Leaders,

            The upload window is open now!
            You can upload your team's binary 30 minutes before the game round starts.

            You can check the timing of the rounds on the information board.
            https://docs.google.com/

Best Regards,
SS2DTMR
RoboCup20XX Committee
            '''
            subject = "The Upload window is OPEN"
        else:
            message = '''Dear Team Leaders,

            Unfortunately, You can not upload a new binary until we open the next uploading window.

            You can check the timing of the rounds on the information board.
            https://docs.google.com/

Best Regards,
SS2DTMR
RoboCup20XX Committee
            '''
            subject = "The Upload window is CLOSE"
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = Team.objects.values_list('email', flat=True).distinct()
        if len(recipient_list) != 0:
            try:
                send_mail(f'Uploading Status | {subject}',message,email_from,recipient_list)

                # send_mail(f'Uploading Status | {subject}',html_message=message,from_email=email_from,recipient_list=recipient_list)

            except Exception as e:
                str_error = traceback.format_exc()
                log_event(request, EventStatus.ERROR, {'error': str_error}, log_id)
        upload_status.changer = request.user
        upload_status.change_date = django.utils.timezone.now()
        upload_status.save()
        log_event(request, EventStatus.COMPLETE, '', log_id)
    return HttpResponse('')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def change_long_test_status(request):
    log_id = log_event(request, EventStatus.STARTING, '')
    if request.method == 'POST':
        if LongTestStatus.objects.all().count() == 0:
            long_test_status = LongTestStatus()
        else:
            long_test_status = LongTestStatus.objects.all().order_by('-change_date')[0]
        long_test_status.status = request.POST.get('long_test_status') == 'true'

        long_test_status.changer = request.user
        long_test_status.change_date = django.utils.timezone.now()
        long_test_status.save()
        log_event(request, EventStatus.COMPLETE, '', log_id)
    return HttpResponse('')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def event_viewer(request):
    all_events = Event.objects.all().order_by("-id")[:30]
    #all_events = all_events[len(all_events)-21:len(all_events)-1]
    total_obj = Event.objects.count()
    return render(request, 'event_viewer.html', {'events': all_events, 'total_obj': total_obj, 'load_more': True})

@user_passes_test(lambda u: u.is_superuser)
def event_viewer_load_all(request):
    redirect('event_viewer')
    all_events = Event.objects.all().order_by("-id")
    total_obj = Event.objects.count()
    return render(request, 'event_viewer.html', {'events': all_events, 'total_obj': total_obj, 'load_more': False})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def event_viewer_load_more(request):
    try:
        offset = request.GET.get('offset')
        offset_int = int(offset)
        limit = 25
        # post_obj = Post.objects.all()[offset_int:offset_int+limit]
        event_obj = list(Event.objects.order_by("-id").values()[offset_int:offset_int+limit])
        data = {
            'events': event_obj
        }
        return JsonResponse(data=data)
    except:
        return JsonResponse({'data': ''})


@login_required
def meet_the_team(request):
    return render(request, 'our_team.html')
