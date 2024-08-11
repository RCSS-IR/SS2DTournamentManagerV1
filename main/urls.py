from django.urls import path
from django.conf.urls import handler404, handler500, handler403, handler400

from . import views

handler400 = 'main.views.error_400'
handler403 = 'main.views.error_403'
handler404 = 'main.views.error_404'
handler500 = 'main.views.error_500'

urlpatterns = [
    path('', views.get_home_iframe, name='home'),
    path('teams', views.get_teams_view, name='get_teams_view'),
    path('teams/add_team', views.add_team_view, name='add_team_view'),
    path('teams/edit_team/<int:id>', views.edit_team, name='edit_team'),
    path('teams/del_team/<int:id>', views.del_team, name='del_team'),
    path('teams/export-csv', views.csv_teams_export, name='csv_teams_export'),

    path('upload_page', views.upload_team_view, name='upload_team_view'),
    path('download_log/<int:id>', views.download_log, name='download_log'),
    path('download_out/<int:id>', views.download_out, name='download_out'),
    path('download_binary/<int:id>', views.download_binary, name='download_binary'),
    path('submit_bin/<int:id>', views.submit_bin, name='submit_bin'),
    path('check_bin/<int:id>', views.check_bin, name='check_bin'),

    path('control_panel', views.control_panel, name='control_panel'),
    path('control_panel/add_iframe', views.add_iframe, name='add_iframe'),
    path('control_panel/init_dtr', views.init_dtr, name='init_dtr'),
    path('control_panel/del_iframe/<int:id>',views.del_iframe, name='del_iframe'),
    path('change_upload_status', views.change_upload_status,
         name='change_upload_status'),
    path('change_long_test_status', views.change_long_test_status,
         name='change_long_test_status'),
    path('kill_server/<str:server_id>', views.kill_server, name='kill_server'),

    path('event_viewer', views.event_viewer, name='event_viewer'),
    path('event_viewer/load', views.event_viewer_load_more, name='event_viewer_load_more'),
    path('event_viewer/load_all', views.event_viewer_load_all, name='event_viewer_load_all'),
    
    path('meet_the_team', views.meet_the_team, name='meet_the_team'),

]
