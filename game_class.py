import pygame
import math
import random

class Game:
        
    def __init__(self, ai = False):

        pygame.init()
        self.running = True
        self.game_over = False
        self.fps = 60
        self.fps_clock = pygame.time.Clock()
        self.menu = True
        self.main_menu = True
        self.screen_ratio = (16,9)
        self.ai = ai

        self._setup_screen()
        self._setup_elements()
        self._setup_audio()
        self._setup_fonts()
                    
    class Player(pygame.sprite.Sprite):
        
        def __init__(self, screen, scale, fps = 120, facing_left = False):

            # Call the parent class (Sprite) constructor
            pygame.sprite.Sprite.__init__(self)

            self.screen = screen
            self.scale = scale
            self.fps = fps
            self.ground = round(self.screen.get_height()*0.78)

            # sprites
            self.sprite = pygame.image.load('sprites/blue_player.png').convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, self.scale((50,50)))
            self.rect = self.sprite.get_rect()

            self.sword_sprite = pygame.image.load('sprites/sword.png').convert_alpha()
            self.sword_sprite = pygame.transform.scale(self.sword_sprite, self.scale((75,30)))
            self.sword_rect = self.sword_sprite.get_rect()
            
            self.downstrike_sprite = pygame.transform.rotate(self.sword_sprite,-90)
            self.downstrike_rect = self.downstrike_sprite.get_rect()

            self.shield_sprite = pygame.image.load('sprites/shield.png').convert_alpha()
            self.shield_sprite = pygame.transform.scale(self.shield_sprite, self.scale((5,50)))
            self.shield_rect = self.shield_sprite.get_rect()
            
            # positioning
            self.rect.left = self.scale(100)
            self.rect.bottom = self.ground
            self.X_change = 0
            self.Y_change = 0
            self.speed = self.scale(8)

            # jumping
            self.jumping = False
            self.jump_speed = self.scale([0,0,-20,-50,-50,-30,-15,-5,-5,-2,-2,0,0,0,0])
            self.jump_fps_time = len(self.jump_speed)
            self.jump_counter = self.jump_fps_time

            # falling
            self.falling = False
            self.fall_ticker = 0
            self.initial_fall_speed = self.scale(3)
            self.on_top = False

            # dashing
            self.most_recent_press = False
            self.press_state = 0
            self.press_time = .1
            self.press_timer = 0
            self.dashing = False
            self.dash_mod = -1
            self.dash_speed = self.scale([0,-30,-30,-30,-30,-30,-30])
            self.dash_fps_time = len(self.dash_speed) 
            self.dash_counter = self.dash_fps_time

            # knockback
            self.knockback = False
            self.knockback_time = .125
            self.knockback_counter = self.knockback_time*self.fps
            self.knockback_speed = self.scale(15)
            
            # striking
            self.sword_hurtbox = False
            self.striking = False
            
            self.sword_time = .2
            self.sword_fps_time = self.sword_time*self.fps
            self.sword_come_out_time = self.sword_fps_time - .02*self.fps
            self.sword_come_in_time = .08*self.fps
            
            self.sword_offsetx = self.scale(50)
            self.sword_offsety = self.scale(-10)
            self.sword_rect.x = self.rect.x+self.sword_offsetx
            self.sword_rect.y = self.rect.y-self.sword_offsety

            # downstrike
            self.downstriking = False
            self.downstrike_offsetx = self.scale(10)
            self.downstrike_offsety = self.scale(-30)
            self.downstrike_rect.x = self.rect.x+self.downstrike_offsetx
            self.downstrike_rect.y = self.rect.y-self.downstrike_offsety
            self.land_downstrike_stun_time_long = 60
            self.land_downstrike_stun_time_short = 10
            self.land_downstrike_stun = False

            # shield
            self.shield_offsetx = self.scale(50)
            self.shield_offsety = 0
            self.shield_rect.x = self.rect.x+self.shield_offsetx
            self.shield_rect.y = self.rect.y-self.shield_offsety
            self.shielding = False
            self.shield_block = False
            self.shield_time = .24
            self.shield_fps_time = self.shield_time*self.fps

            # stamina
            self.max_stamina = 5
            self.stamina = 5
            self.stamina_reload_time = .4
            self.stamina_reload_counter = self.stamina_reload_time*self.fps

            # other attributes
            self.life = 5
            self.invinsible = False
            self.i_frames = 60
            self.i_frames_invinsible = True

            # sounds
            self.shield_sound = pygame.mixer.Sound('sprites/sounds/shield.mp3')
            self.sword_swoosh_sound = pygame.mixer.Sound('sprites/sounds/sword_swoosh.wav')
            self.sword_hit_ground_sound = pygame.mixer.Sound('sprites/sounds/sword_hit_ground.wav')
            self.jump_sound = pygame.mixer.Sound('sprites/sounds/jump.mp3')
            self.land_sound = pygame.mixer.Sound('sprites/sounds/land.mp3')
            self.dash_sound = pygame.mixer.Sound('sprites/sounds/dash.mp3')

            # input keys
            self.input_dict = {
                'jump': pygame.K_w,
                'left': pygame.K_a,
                'right': pygame.K_d,
                'down': pygame.K_s,
                'sword': pygame.K_f,
                'shield': pygame.K_g
            }

            self.facing_left = facing_left
            if self.facing_left is True:
                self.sprite = pygame.image.load('sprites/red_player.png').convert_alpha()
                self.sprite = pygame.transform.scale(self.sprite, self.scale((50,50)))
                self.flip_player()
                self.rect.right = self.screen.get_width()-self.scale(100)
                self.input_dict = {
                    'jump': pygame.K_UP,
                    'left': pygame.K_LEFT,
                    'right': pygame.K_RIGHT,
                    'down': pygame.K_DOWN,
                    'sword': pygame.K_h,
                    'shield': pygame.K_j
                }
        
        def show(self):
            '''Show character sprite.'''

            self.screen.blit(self.sprite, (self.rect.x, self.rect.y))

        def update(self):
            '''Handle events that must take place every frame.'''

            self.continue_knockback()
            self.continue_dash()
            self.continue_jump()
            self.check_fall()
            self.continue_fall()
            self.stamina_update()
            self.continue_strike()
            self.continue_downstrike()
            self.continue_land_downstrike()
            self.continue_shield()
            self.continue_iframes()
            self.iterate_dash_timer()

        def movement(self):
            '''Handle sprite movements.'''

            self.rect.move_ip(self.X_change,self.Y_change)

            if self.rect.x <= 0:
                self.rect.x = 0
            elif self.rect.right >= self.screen.get_width():
                self.rect.right = self.screen.get_width()       

            if self.rect.bottom > self.ground:
                self.rect.bottom = self.ground

        def flip_player(self):
            
            self.sprite = pygame.transform.flip(self.sprite, True, False)
            self.sword_sprite = pygame.transform.flip(self.sword_sprite, True, False)
            self.shield_sprite = pygame.transform.flip(self.shield_sprite, True, False)
            self.sword_offsetx = (self.sword_offsetx+self.scale(25))*-1
            self.shield_offsetx = (self.shield_offsetx-self.scale(45))*-1
            self.dash_mod *= -1

        def check_fall(self):

            if (self.rect.bottom < self.ground) & (self.jumping is False) & (self.on_top is False):
                self.deploy_fall()

        def deploy_fall(self):
            
            if self.falling is False:
                self.falling = True
                self.fall_ticker = 1

        def continue_fall(self):

            if (self.rect.bottom == self.ground) or (self.on_top is True):
                self.falling = False
                if self.Y_change >= 0:
                    self.Y_change = 0

            if self.falling is True:
                if self.fall_ticker < 10:
                    self.fall_ticker += 1
                self.Y_change = self.initial_fall_speed*self.fall_ticker

        def deploy_jump(self):
            
            if (self.jumping is False) & (self.falling is False):
                
                self.jumping = True
                self.jump_counter = self.jump_fps_time
                self.jump_sound.play()
                
        def continue_jump(self):

            if self.jumping is True:
                if self.jump_counter <= 0:
                    self.jumping = False
                else:
                    timer = int(self.jump_fps_time - self.jump_counter)
                    self.Y_change = self.jump_speed[timer]
                    self.jump_counter -= 1

        def deploy_knockback(self):
            
            if self.knockback is False:
                self.knockback = True
                self.X_change = self.knockback_speed
                self.knockback_counter = self.knockback_time*self.fps
        
        def continue_knockback(self):

            if self.knockback is True:
                self.knockback_counter -= 1
                
                if self.knockback_counter <= 0:
                    self.knockback = False
                    self.X_change = 0
                else:
                    self.X_change = self.knockback_speed
        
        def check_dash(self, press=None):
            
            # if something is pressed
            if press is not None:
                # if ready
                if self.press_state == 0:
                    # get ready to look for upkey
                    self.press_state +=1
                    # start timer
                    self.press_timer = self.press_time*self.fps
                    # set press id
                    self.most_recent_press = press
                # if down up down within timer
                if (self.press_state == 2):
                    # if within timer window
                    if self.press_timer > 0:
                        # if press equals first press
                        if self.most_recent_press == press:
                            self.deploy_dash()
                    # always restart after stage 2
                    self.press_state = 0
            # if nothing is pressed and press_state is ready for upkey
            if (press is None) & (self.press_state == 1):
                self.press_state += 1
            #if timer is up, return to state 0
            if self.press_timer == 0:
                self.press_state = 0

        def iterate_dash_timer(self):

            if self.press_timer > 0:
                self.press_timer -= 1

        def deploy_dash(self):

            if (self.is_acting() is False) & (self.stamina > 0):
                self.X_change = self.dash_speed[0]*self.dash_mod
                self.dash_counter = self.dash_fps_time
                self.dashing = True
                self.dash_sound.play()

                self.stamina -= 1
                self.stamina_reload_counter = self.stamina_reload_time*self.fps
        
        def continue_dash(self):
            
            if self.dashing is True:
                if self.dash_counter <= 0:
                    self.dashing = False
                    self.X_change = 0
                else:
                    timer = int(self.dash_fps_time - self.dash_counter)
                    self.X_change = self.dash_speed[timer]*self.dash_mod
                    self.dash_counter -= 1

        def stamina_update(self):
            if (self.stamina < self.max_stamina) & (self.jumping is False):
                self.stamina_reload_counter -= 1
                if self.stamina_reload_counter <= 0:
                    self.stamina += 1
                    self.stamina_reload_counter = self.stamina_reload_time*self.fps 
        
        def deploy_strike(self):
            '''Deploys sword strike and starts timer.'''

            if (self.is_acting() is False) & (self.stamina > 0):
                self.sword_swoosh_sound.play()
                self.striking = True
                self.striking_counter = self.sword_fps_time
                
                self.stamina -= 1
                self.stamina_reload_counter = self.stamina_reload_time*self.fps
                
        def continue_strike(self):
            '''Handles sword strike including sprite, frozen frames, and timer countdown'''

            if self.striking is True:

                self.striking_counter -= 1

                if self.sword_come_in_time < self.striking_counter < self.sword_come_out_time:
                    self.screen.blit(self.sword_sprite, (self.rect.x+self.sword_offsetx, self.rect.y-self.sword_offsety))
                    self.sword_rect.x = self.rect.x+self.sword_offsetx
                    self.sword_rect.y = self.rect.y-self.sword_offsety
                    self.sword_hurtbox = True
                else:
                    self.sword_hurtbox = False
                
                if self.striking_counter <= 0:
                    self.striking = False

        def deploy_downstrike(self):

            if (self.is_acting() is False) & (self.stamina > 0):
                if (self.jumping) or (self.falling):
                    self.X_change = 0
                    self.jumping = False
                    self.sword_swoosh_sound.play()
                    self.downstriking = True
                    
                    self.stamina -= 1
                    self.stamina_reload_counter = self.stamina_reload_time*self.fps

        def continue_downstrike(self):

            if self.downstriking is True:

                if self.falling is True:
                    self.X_change = 0
                    self.screen.blit(self.downstrike_sprite, (self.rect.x+self.downstrike_offsetx, self.rect.y-self.downstrike_offsety))
                    self.downstrike_rect.x = self.rect.x+self.downstrike_offsetx
                    self.downstrike_rect.y = self.rect.y-self.downstrike_offsety
                
                else:
                    self.downstriking = False
                    
                    if self.on_top is True: 
                        self.deploy_land_downstrike(self.land_downstrike_stun_time_short)
                    else:
                        self.deploy_land_downstrike(self.land_downstrike_stun_time_long)

        def deploy_land_downstrike(self, timer):
            self.sword_hit_ground_sound.play()
            self.land_downstrike_stun = True
            self.land_downstrike_timer = timer
            self.X_change = 0
        
        def continue_land_downstrike(self):

            if self.land_downstrike_stun is True:
                if self.land_downstrike_timer > 0:
                    self.land_downstrike_timer -= 1
                else:
                    self.land_downstrike_stun = False

        def deploy_shield(self):
            
            if (self.is_acting() is False) & (self.stamina > 0):
                self.shield_sound.play()
                self.shielding = True
                self.shield_counter = self.shield_fps_time
                
                self.stamina -= 1
                self.stamina_reload_counter = self.stamina_reload_time*self.fps
                
                self.X_change = 0
        
        def continue_shield(self):

            if self.shielding is True:

                self.shield_counter -= 1
                self.screen.blit(self.shield_sprite, (self.rect.x+self.shield_offsetx, self.rect.y-self.shield_offsety))
                self.shield_rect.x = self.rect.x+self.shield_offsetx
                self.shield_rect.y = self.rect.y-self.shield_offsety
                self.shield_block = True
                
                if self.shield_counter <= 0:
                    self.shielding = False
                    self.shield_block = False

        def deploy_iframes(self):

            self.invinsible = True
            self.i_frames_invinsible = True
            self.i_frames = 60

        def continue_iframes(self):
            '''Handles counting down invinsibility frames.'''
            
            if self.i_frames_invinsible is True: 
                self.i_frames -= 1
                if self.i_frames <= 0:
                    self.invinsible = False
                    self.i_frames_invinsible = False
                    self.i_frames = 60
        
        def take_hit(self, knockback = True):
            self.life -= 1
            if knockback is True:
                self.deploy_knockback()
            self.deploy_iframes()
            
        def is_ready(self):
            '''Returns True if player is ready for new inputs.'''
            if (self.knockback is False) & (self.land_downstrike_stun is False):
                return True
            return False
        
        def is_acting(self):

            if (self.striking is True) or (self.downstriking is True) or (self.shielding is True) or (self.dashing is True):
                return True
            return False

    class AIEnemy():
        
        def __init__(
            self, 
            input_dict,
            playera,
            playerb, 
            ai_scheme = 'heuristic'):

            self.ai_scheme = ai_scheme
            self.playera = playera
            self.playerb = playerb

            self.input_dict = input_dict
            self.ai_key_dict = {
                self.input_dict['jump']:0,
                self.input_dict['left']:0,
                self.input_dict['right']:0,
                self.input_dict['down']:0,
                self.input_dict['sword']:0,
                self.input_dict['shield']:0}

            if ai_scheme != 'random_input':

                self.walk_left = [self.input_dict['left']]*10
                self.walk_right = [self.input_dict['right']]*10
                self.sword = [self.input_dict['sword']]
                self.shield = [self.input_dict['shield']]
                self.jump_left = [self.input_dict['jump']] + self.walk_left
                self.jump_right = [self.input_dict['jump']] + self.walk_right
                self.jump_left_downstrike = self.jump_left + [self.input_dict['down']]
                self.jump_right_downstrike = self.jump_right + [self.input_dict['down']]
                
                self.sequence_index = 0
                self.sequence_list = [
                    self.walk_left, 
                    self.walk_right,
                    self.sword, self.sword, self.sword,
                    self.shield, self.shield, self.shield,
                    self.jump_left_downstrike,
                    self.jump_right_downstrike
                    ]
                self.sequence = self.walk_left

        def get_input(self):

            if self.ai_scheme == 'random_input':
                return self._random_input()
            elif self.ai_scheme == 'random_sequence':
                return self._random_sequence()
            elif self.ai_scheme == 'heuristic':
                return self._heuristics()

        def _random_input(self):
        
            ai_key_dict_copy = self.ai_key_dict.copy()
            ai_key_dict_copy[random.sample(self.ai_key_dict.keys(),1)[0]] = 1
            
            return ai_key_dict_copy
        
        def _random_sequence(self):

            if self.sequence_index == len(self.sequence)-1:
                self.sequence = random.sample(self.sequence_list,1)[0]
                self.sequence_index = 0
            else:
                self.sequence_index += 1

            input = self.sequence[self.sequence_index]
            
            ai_key_dict_copy = self.ai_key_dict.copy()
            ai_key_dict_copy[input] = 1
            
            return ai_key_dict_copy
        
        def _heuristics(self):
            
            if self.sequence_index == len(self.sequence)-1:
                self.sequence = self._choose_heuristic()
                self.sequence_index = 0
            else:
                self.sequence_index += 1

            input = self.sequence[self.sequence_index]
            
            ai_key_dict_copy = self.ai_key_dict.copy()
            ai_key_dict_copy[input] = 1
            
            return ai_key_dict_copy

        def _choose_heuristic(self):

            # far away
            if self._is_left() & self._is_far() & self._has_stamina():
                sequence = self.walk_left
            elif self._is_right() & self._is_far() & self._has_stamina():
                sequence = self.walk_right
            # close
            elif self._is_left() & self._is_close() & self._has_stamina():
                possible_sequences = [self.walk_left,self.sword,self.shield]
                sequence = random.sample(possible_sequences,1)[0]
            elif self._is_right() & self._is_close() & self._has_stamina():
                possible_sequences = [self.walk_right,self.sword,self.shield]
                sequence = random.sample(possible_sequences,1)[0]
            # medium distance
            elif self._is_left() & self._is_medium() & self._has_stamina():
                sequence = self.jump_left_downstrike
            elif self._is_right() & self._is_medium() & self._has_stamina():
                sequence = self.jump_right_downstrike
            # no stamina
            elif self._is_left() & (not self._has_stamina()):
                possible_sequences = [self.walk_right,[None]*10]
                sequence = random.sample(possible_sequences,1)[0]
            elif self._is_right() & (not self._has_stamina()):
                possible_sequences = [self.walk_left,[None]*10]
                sequence = random.sample(possible_sequences,1)[0]
            else:
                sequence = [None]
            
            return sequence
        
        def _is_left(self):
            return self.playera.rect.centerx < self.playerb.rect.centerx

        def _is_right(self):
             return self.playera.rect.centerx > self.playerb.rect.centerx
            
        def _is_far(self, distance = 160):
            return abs(self.playera.rect.centerx - self.playerb.rect.centerx) > self.playera.scale(distance)
        
        def _is_close(self, distance = 140):
            return abs(self.playera.rect.centerx - self.playerb.rect.centerx) < self.playera.scale(distance)

        def _is_medium(self, low_distance = 140, high_distance = 160):
            return (not self._is_far(high_distance)) & (not self._is_close(low_distance))
        
        def _has_stamina(self):
            return self.playerb.stamina > 0

    def scale(self, val):
        
        # divide by 60 is so I can pass same values as before scaling was implemented
        if isinstance(val,(int,float)):
            return math.floor((val/60)*self.scale_factor)
        if isinstance(val,(list,tuple)):
            return [math.floor((i/60)*self.scale_factor) for i in val]

    def _setup_screen(self):
        '''Creates pygame screen and draws background.'''

        monitor_size = (pygame.display.Info().current_w,pygame.display.Info().current_h)
        # monitor_size = (1000,700)
        
        horiz = monitor_size[0]/self.screen_ratio[0]
        vert = monitor_size[1]/self.screen_ratio[1]
        self.scale_factor = min(horiz,vert)
        self.screen_size = (math.floor(self.scale_factor*self.screen_ratio[0]),math.floor(self.scale_factor*self.screen_ratio[1]))

        self.screen = pygame.display.set_mode(self.screen_size)
        
        # title and icon
        pygame.display.set_caption('Battle')

        self.blue_heart_sprite = pygame.image.load('sprites/blue_heart.png').convert_alpha()
        self.blue_heart_sprite = pygame.transform.scale(self.blue_heart_sprite, self.scale((30,30)))
        self.red_heart_sprite = pygame.image.load('sprites/red_heart.png').convert_alpha()
        self.red_heart_sprite = pygame.transform.scale(self.red_heart_sprite, self.scale((30,30)))        
        self.stamina_sprite = pygame.image.load('sprites/stamina.png').convert_alpha()
        self.stamina_sprite = pygame.transform.scale(self.stamina_sprite, self.scale((60,60)))

    def _setup_audio(self):

        self.sword_hit_sound = pygame.mixer.Sound('sprites/sounds/sword_hit.mp3')
        self.sword_hit_shield_sound = pygame.mixer.Sound('sprites/sounds/sword_hit_shield.wav')
        self.sword_hit_shield_sound.set_volume(.3)
        
    def update_display(self):
        pygame.display.update()
        self.fps_clock.tick(self.fps)

    def show_background(self):
        '''Draws background.'''
        self.screen.fill((0,0,0))
        pygame.draw.rect(self.screen,(255,255,255),(0,self.screen_size[1]*.78, self.screen_size[0],self.scale(10)))

    def _setup_elements(self):
        '''Creates character and environment elements.'''

        self.player1 = self.Player(self.screen, self.scale, facing_left = False)
        self.player2 = self.Player(self.screen, self.scale, facing_left = True)

        if self.ai is True:
            self.ai_enemy = self.AIEnemy(
                self.player2.input_dict,
                self.player1, self.player2, 
                ai_scheme = 'heuristic')

    def _setup_fonts(self):
        '''Creates fonts for various texts.'''

        self.score_font = pygame.font.Font('freesansbold.ttf', self.scale(32))
        self.over_font = pygame.font.Font('freesansbold.ttf', self.scale(48))

    def handle_menu(self):

        if (self.main_menu is True) & (self.running is True):

            self.show_background()
            self.player1.show()
            self.player2.show()
            self._show_menu()
            
            keys = (pygame.event.get(pygame.KEYDOWN))
            if len(keys) > 0:
                if keys[0].key == self.player1.input_dict['right']:
                    if self.player1.life < 9:
                        self.player1.life += 1
                        self.player1.stamina -= 1
                        self.player1.max_stamina -=1

                if keys[0].key == self.player1.input_dict['left']:
                    if self.player1.stamina < 9:
                        self.player1.life -= 1
                        self.player1.stamina += 1
                        self.player1.max_stamina +=1

                if keys[0].key == self.player2.input_dict['left']:
                    if self.player2.life < 9:
                        self.player2.life += 1
                        self.player2.stamina -= 1
                        self.player2.max_stamina -=1

                if keys[0].key == self.player2.input_dict['right']:
                    if self.player2.stamina < 9:
                        self.player2.life -= 1
                        self.player2.stamina += 1
                        self.player2.max_stamina += 1
                
                if keys[0].key == pygame.K_SPACE:
                    self.menu = False
            
            self.player1.rect.bottom = self.player1.ground
            self.player2.rect.bottom = self.player2.ground

    def _show_menu(self):

        self._show_lives()
        self._show_stamina()

        space_text = self.over_font.render('Press SPACE to start', True, (255,255,255))
        stats_text = self.over_font.render("Use keys to adjust your fighter's stats", True, (255,255,255))

        half_width,half_height = self.screen_size[0]/2,self.screen_size[1]/2

        space_text_rect = space_text.get_rect(center=(half_width,half_height*.5))
        self.screen.blit(space_text, space_text_rect)

        stats_text_rect = stats_text.get_rect(
            midtop=(half_width,space_text_rect.bottom+half_height*.03))
        self.screen.blit(stats_text, stats_text_rect)

    def show_data(self):

        self._show_lives()
        self._show_stamina()

    def _show_lives(self):

        self.screen.blit(self.blue_heart_sprite, self.scale((15, 23)))
        self.screen.blit(self.red_heart_sprite, self.scale((925,23)))

        y = self.scale(23)
        size = self.scale(30)

        for i in range(self.player1.life):
            x = self.scale(60) + self.scale(30)*i
            pygame.draw.rect(self.screen,(99,155,255),[x, y, size, size])
        for i in range(self.player2.life):
            x = self.screen_size[0]-self.scale(80)-self.scale(30)*i
            pygame.draw.rect(self.screen,(217,87,99),[x, y, size, size])

    def _show_stamina(self):

        y = self.scale(70)
        size = self.scale(30)

        for i in range(self.player1.stamina):
            x = self.scale(60) + self.scale(30)*i
            pygame.draw.rect(self.screen,(255,255,255),[x, y, size, size])
        for i in range(self.player2.stamina):
            x = self.screen_size[0]-self.scale(80)-self.scale(30)*i
            pygame.draw.rect(self.screen,(255,255,255),[x, y, size, size])
        
        self.screen.blit(self.stamina_sprite, self.scale((0, 50)))
        self.screen.blit(self.stamina_sprite, self.scale((905, 50)))

    def handle_events(self):
        '''Quits game if exit is pressed.'''

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
        
            if event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h),
                                                    pygame.RESIZABLE)
                self.player1.ground = round(self.screen.get_height()*0.78)
                self.player2.ground = round(self.screen.get_height()*0.78)
                over_font_size = round(min(self.screen.get_width()*.08,self.screen.get_height()*.08))
                self.over_font = pygame.font.Font('freesansbold.ttf', over_font_size)

    def handle_gameover(self):

        self._check_game_over()
        self._handle_reset()

    def _check_game_over(self):
        
        if self.player1.life <= 0:

            self._show_game_over('Player 2 wins')
            self.player1.rect.y = -2000
            self.player1.knockback = True
            self.game_over = True

        if self.player2.life <= 0:

            self._show_game_over('Player 1 wins')
            self.player2.rect.y = -2000
            self.player2.knockback = True
            self.game_over = True 
    
    def _show_game_over(self, text):

        over_text = self.over_font.render(text, True, (255,255,255))
        restart_text = self.over_font.render('Press SPACE to restart', True, (255,255,255))
        reset_text = self.over_font.render('Press R to reset stats', True, (255,255,255))

        half_width,half_height = self.screen.get_width()/2,self.screen.get_height()/2

        over_text_rect = over_text.get_rect(center=(half_width,half_height*.5))
        self.screen.blit(over_text, over_text_rect)

        restart_text_rect = restart_text.get_rect(midtop=(half_width,over_text_rect.bottom+half_height*.03))
        self.screen.blit(restart_text, restart_text_rect)

        reset_text_rect = reset_text.get_rect(midtop=(half_width,restart_text_rect.bottom+half_height*.03))
        self.screen.blit(reset_text, reset_text_rect)
    
    def _handle_reset(self):

        if self.game_over is True:

            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                self.game_over = False
                max_stamina1 = self.player1.max_stamina
                max_stamina2 = self.player2.max_stamina

                self._setup_elements()
                self.player1.max_stamina,self.player1.stamina,self.player1.life = max_stamina1,max_stamina1,10-max_stamina1
                self.player2.max_stamina,self.player2.stamina,self.player2.life = max_stamina2,max_stamina2,10-max_stamina2
            
            if keys[pygame.K_r]:
                self.game_over = False
                self.menu = True
                self._setup_elements()

    def handle_input(self):

        keys = pygame.key.get_pressed()
        self._player_movement(self.player1, keys)
        
        if self.ai is True:
            ai_input = self.ai_enemy.get_input()
            if ai_input is not None:
                keys = ai_input
        
        self._player_movement(self.player2, keys)

    def _player_movement(self, player, keys):

        if player.is_ready():
            # left movement
            if keys[player.input_dict['left']]:
            
                if player.facing_left is False:
                    player.facing_left = True
                    player.flip_player()

                player.X_change = -player.speed
                player.check_dash('Left')
            
            # right movement
            if keys[player.input_dict['right']]:

                if player.facing_left is True:
                    player.facing_left = False
                    player.flip_player()

                player.X_change = player.speed
                player.check_dash('Right')
                        
            # jumping
            if keys[player.input_dict['jump']]:
                player.deploy_jump()
            
            # downstrike
            if keys[player.input_dict['down']]:
                player.deploy_downstrike()

            # sword
            if (keys[player.input_dict['sword']]):
                player.deploy_strike()
            
            # shield
            if keys[player.input_dict['shield']]:
                player.deploy_shield()

            # stopping
            if keys[player.input_dict['right']] and keys[player.input_dict['left']]: 
                player.X_change = 0
            if not keys[player.input_dict['right']] and not keys[player.input_dict['left']]:
                player.X_change = 0
                player.check_dash()

    def handle_collisions(self):
        '''Handles collisions from both players and swords.'''
        
        self._handle_sword_collisions()
        self._handle_player_collisions()
        self._handle_downstrike_collisions()

    def _handle_player_collisions(self):
        '''Handles player collisions.'''
        
        # check collision between 2 players
        collide = bool(self.player1.rect.colliderect(self.player2.rect))

        if collide is True:
            self._calc_player_collision(self.player1, self.player2)
            self._calc_player_collision(self.player2, self.player1)
        else:
            self.player1.on_top = False
            self.player2.on_top = False
            
    def _calc_player_collision(self,playera,playerb):
        
        playera.on_top = self._edge_detection(playera.rect.bottom, playerb.rect.top)

        if (playera.on_top is False) & (playerb.on_top is False):
            if playera.rect.x < playerb.rect.x:
                if playera.X_change > 0:
                    playera.X_change = 0
                if playerb.X_change < 0:
                    playerb.X_change = 0
        
        # if player a is above player b
        if playera.rect.y < playerb.rect.y:
            # player a can't fall, player b can't jump
            if playera.Y_change > 0:
                playera.Y_change = 0
            if playerb.Y_change < 0:
                playerb.Y_change = 0
        
        if playera.on_top is True:
            playera.rect.bottom = playerb.rect.top+1
            self._edge_detection(playera.rect.bottom, playerb.rect.top)
    
    def _edge_detection(self,edgea,edgeb,margin=30):

        return abs(edgea - edgeb) < self.scale(margin)

    def _handle_sword_collisions(self):

        self._calc_sword_collisions(self.player1, self.player2)
        self._calc_sword_collisions(self.player2, self.player1)

    def _calc_sword_collisions(self, playera, playerb):
        
        # if sword is deployed
        if playera.sword_hurtbox is True:
            
            # check collisions
            playerb_collide = bool(playera.sword_rect.colliderect(playerb.rect))
            
            if playerb.shielding is True:
                shieldb_collide = bool(playera.sword_rect.colliderect(playerb.shield_rect))
            else:
                shieldb_collide = False
            
            # calc left/right for knockback
            if playera.rect.centerx < playerb.rect.centerx:
                playerb.knockback_speed = abs(playerb.knockback_speed)
                playera.knockback_speed = -abs(playerb.knockback_speed)
            else:
                playerb.knockback_speed = -abs(playerb.knockback_speed)
                playera.knockback_speed = abs(playerb.knockback_speed)
            
            # hit shield and not player
            if shieldb_collide and not playerb_collide:
                self.do_shield_hit(playera)

            # hit player
            if playerb_collide:
                
                if playera.rect.centerx < playerb.rect.centerx:
                    if (playerb.facing_left) and (playerb.shield_block):
                        self.do_shield_hit(playera)
                    else:
                        self.do_hit(playerb)

                if playera.rect.centerx > playerb.rect.centerx:
                    if (not playerb.facing_left) and (playerb.shield_block):
                        self.do_shield_hit(playera)
                    else:
                        self.do_hit(playerb)
    
    def _handle_downstrike_collisions(self):

        self._calc_downstrike_collisions(self.player1, self.player2)
        self._calc_downstrike_collisions(self.player2, self.player1)

    def _calc_downstrike_collisions(self, playera, playerb):
        
        # if sword is deployed
        if playera.downstriking is True:
            
            # check collisions
            playerb_collide = bool(playera.downstrike_rect.colliderect(playerb.rect))

            # hit player
            if playerb_collide:
                self.do_hit(playerb,knockback=False)

    def do_hit(self, player, knockback=True):
        if player.invinsible is False: 
            player.take_hit(knockback)
            self.sword_hit_sound.play()
    
    def do_shield_hit(self,player):
        if player.knockback is False:
            player.stamina = 0
            self.sword_hit_shield_sound.play()
            player.deploy_knockback()

if __name__ == "__main__":
    
    game = Game(ai = True)

    while game.running is True:

        if game.menu is True:
            game.handle_menu()

        else:
            game.show_background()
            
            game.handle_gameover()
            game.handle_input()

            game.player1.update()
            game.player2.update()

            game.handle_collisions()

            game.player1.movement()
            game.player2.movement()

            game.player1.show()
            game.player2.show()
            game.show_data()
        
        game.handle_events()  
        game.update_display()