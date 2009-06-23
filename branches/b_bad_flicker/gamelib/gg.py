# globals. For sanity only add things that do not change from the end of startup
# to the end of session.

# available services (callables with no params) registers there;
# convention : services['s_foo'] = foo
services = {}

#consts to tweak gameplay
zombie_spawn_recovery_time = 1.0
zombie_spawn_attack_damage = 20
zombie_spawn_retry_time = 0.5

powerup_spawn_retry_time = 0.5

#top_speed = 430.0 # 800. parece mucho, pero 430 parece poco
top_speed = 600.0
accel_factor = 300.0
player_max_life = 100.0
##zombie_art_radius = 40.0
### anchor , body_radius
##boy_bat_idle0 = 61.0, 59.0,  76.0/2.0
##boy_bat_walk0 = 61.0, 59.0,  76.0/2.0
##boy_bat_walk1 = 61.0, 59.0,  76.0/2.0
##
##boy_idle0 = 61.0 , 59.0 , 76.0/2
##boy_walk0 = 61.0 , 59.0 , 76.0/2
##boy_walk2 = 61.0 , 59.0 , 76.0/2
##
##bullet = 6,8, 5/2
##
##father_idle0 = 44, 61.5, 84/2
##1,19,87,104
##
##father_walk0 44,61,5, 84/2.0
##1,19, 87, 106
##
##father_walk1 44,61,5, 84/2.0
##1,19, 87, 106
##
##father_shotgun_idle0 = 43, 54, 84/2
##0,86, 12, 96
##
##father_shotgun_walk0 = 43.5 , 56, 84/2
##1, 86, 13, 96
##
##father_shotgun_walk1 = 43.5 , 54, 84/2
##1 12 86 96
##
##girl_doll_idle0 = 40.5 , 69.0, 40,5  ( same for walk )
##0, 29,81, 109
##
##girl_idle0 = 40, 58, 40
##0, 18,80, 98
##
##zombie_idle0 = 40.5, 62, 84/2 
##1, 20, 86, 104 
##
##
##
