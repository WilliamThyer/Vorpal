import pygame
import math
import random
import copy

class Game:
        
    def __init__(self, ai = False):

        pygame.init()
        self.running = True
        self.game_over = False
        self.fps = 60
        self.fps_clock = pygame.time.Clock()
        self.menu = True

        self._setup_screen()
        self._setup_elements()
        self._setup_audio()
        self._setup_fonts()

        self.ai = ai
        if self.ai is True:
            ai_enemy = self.AIEnemy()
                    
    class Player(pygame.sprite.Sprite):
        
        def __init__(self, screen, fps = 120, facing_left = False):

            # Call the parent class (Sprite) constructor
            pygame.sprite.Sprite.__init__(self)

            self.screen = screen
            self.fps = fps
            self.ground = round(self.screen.get_height()*0.78)

            # sprites
            self.sprite = pygame.image.load('sprites/blue_player.png').convert_alpha()
            self.rect = self.sprite.get_rect()
            self.sword_sprite = pygame.image.load('sprites/sword.png').convert_alpha()
            self.sword_rect = self.sword_sprite.get_rect()
            self.shield_sprite = pygame.image.load('sprites/shield.png').convert_alpha()
            self.shield_rect = self.shield_sprite.get_rect()
            
            # positioning
            self.rect.x = 100
            self.rect.bottom = self.ground
            self.X_change = 0
            self.Y_change = 0
            self.speed = 15

            # jumping
            self.jumping = False
            self.jump_speed = [0,0,-40,-80,-80,-60,-30,-10,-10,-2,-2,0,0,0,0]
            self.jump_fps_time = len(self.jump_speed)
            self.jump_counter = self.jump_fps_time

            # falling
            self.falling = False
            self.fall_ticker = 0
            self.initial_fall_speed = 5
            self.on_top = False

            # dashing
            self.most_recent_press = False
            self.press_state = 0
            self.press_time = .1
            self.press_timer = 0
            self.dashing = False
            self.dash_mod = -1
            self.dash_speed = [0,-40,-50,-50,-50,-50,-50,-40,-40]
            self.dash_fps_time = len(self.dash_speed) 
            self.dash_counter = self.dash_fps_time

            # knockback
            self.knockback = False
            self.knockback_time = .125
            self.knockback_counter = self.knockback_time*self.fps
            self.knockback_speed = 25
            
            # sword
            self.sword_offsetx = 150
            self.sword_offsety = -50 
            self.striking = False
            self.sword_hurtbox = False
            self.sword_time = .2
            self.sword_fps_time = self.sword_time*self.fps
            self.sword_come_out_time = self.sword_fps_time - .02*self.fps
            self.sword_come_in_time = .08*self.fps

            # shield
            self.shield_offsetx = 150
            self.shield_offsety = 0
            self.shielding = False
            self.shield_block = False
            self.shield_time = .24
            self.shield_fps_time = self.shield_time*self.fps
            self.shield_come_out_time = self.shield_fps_time - .02*self.fps
            self.shield_come_in_time = .02*self.fps

            # stamina
            self.max_stamina = 5
            self.stamina = 5
            self.stamina_reload_time = .5
            self.stamina_reload_counter = self.stamina_reload_time*self.fps

            # other attributes
            self.life = 5
            self.invinsible = False
            self.i_frames = 60
            self.i_frames_invinsible = True

            # sounds
            self.shield_sound = pygame.mixer.Sound('sprites/sounds/shield.mp3')
            self.sword_swoosh_sound = pygame.mixer.Sound('sprites/sounds/sword_swoosh.wav')
            self.jump_sound = pygame.mixer.Sound('sprites/sounds/jump.mp3')
            self.land_sound = pygame.mixer.Sound('sprites/sounds/land.mp3')
            self.dash_sound = pygame.mixer.Sound('sprites/sounds/dash.mp3')

            self.facing_left = facing_left
            if self.facing_left is True:
                self.sprite = pygame.image.load('sprites/red_player.png').convert_alpha()
                self.flip_player()
                self.rect.x = 1300
        
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
            self.sword_offsetx = (self.sword_offsetx+15)*-1
            self.shield_offsetx = (self.shield_offsetx-130)*-1
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
            
            if self.jumping is False:
                
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
            if self.stamina < self.max_stamina:
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

                if self.shield_come_in_time < self.shield_counter < self.shield_come_out_time:
                    self.screen.blit(self.shield_sprite, (self.rect.x+self.shield_offsetx, self.rect.y-self.shield_offsety))
                    self.shield_block = True
                    self.invinsible = True
                else:
                    self.shield_block = False
                    self.invinsible = False
                
                if self.shield_counter <= 0:
                    self.shielding = False
                    self.shield_block = False
                    self.invinsible = False

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
            
        def is_ready(self):
            '''Returns True if player is ready for new inputs. (Can be expanded with other elements like self.is_jumping).'''
            
            return not self.knockback
        
        def is_acting(self):

            if (self.striking is True) or (self.shielding is True) or (self.dashing is True):
                return True
            return False

    class AIEnemy():
        
        def __init__(self):

            l,r,u,h,j = pygame.K_LEFT,pygame.K_RIGHT,pygame.K_UP,pygame.K_h,pygame.K_j
            self.ai_key_dict = {l:0,r:0,u:0,h:0,j:0}
        
        def ai_controls(self):
        
            ai_key_dict_copy = copy.copy(self.ai_key_dict)
            ai_key_dict_copy[random.sample(self.ai_key_dict.keys(),1)[0]] = 1
            return ai_key_dict_copy

    def _setup_screen(self):
        '''Creates pygame screen and draws background.'''
        monitor_size = (pygame.display.Info().current_w,pygame.display.Info().current_h-80)
        self.screen = pygame.display.set_mode(monitor_size,pygame.RESIZABLE)
        
        # title and icon
        pygame.display.set_caption('Battle')
        # self.background = pygame.image.load('sprites/background.png').convert()
        # self.background = pygame.transform.scale(self.background, monitor_size)
        

        self.blue_heart_sprite = pygame.image.load('sprites/blue_heart.png').convert_alpha()
        self.blue_heart_sprite = pygame.transform.scale(self.blue_heart_sprite, (30, 30))
        self.red_heart_sprite = pygame.image.load('sprites/red_heart.png').convert_alpha()
        self.red_heart_sprite = pygame.transform.scale(self.red_heart_sprite, (30, 30))        
        self.stamina_sprite = pygame.image.load('sprites/stamina.png').convert_alpha()
        self.stamina_sprite = pygame.transform.scale(self.stamina_sprite, (60, 60))

    def _setup_audio(self):

        self.sword_hit_sound = pygame.mixer.Sound('sprites/sounds/sword_hit.mp3')
        self.sword_hit_shield_sound = pygame.mixer.Sound('sprites/sounds/sword_hit_shield.wav')
        
    def update_display(self):
        pygame.display.update()
        self.fps_clock.tick(self.fps)

    def show_background(self):
        '''Draws background.'''
        self.screen.fill((0,0,0))
        pygame.draw.rect(self.screen,(255,255,255),(0,self.screen.get_height()*.78, self.screen.get_width(),20))

    def _setup_elements(self):
        '''Creates character and environment elements.'''

        self.player1 = self.Player(self.screen, facing_left = False)
        self.player2 = self.Player(self.screen, facing_left = True)

    def _setup_fonts(self):
        '''Creates fonts for various texts.'''

        self.score_font = pygame.font.Font('freesansbold.ttf', 32)
        self.over_font = pygame.font.Font('freesansbold.ttf',64)

    def main_menu(self):

        while (self.menu is True) & (self.running is True):
              
            # need this for inner while loop
            pygame.event.pump()

            self.show_background()
            self.player1.show()
            self.player2.show()
            self._show_menu()
            
            keys = (pygame.event.get(pygame.KEYDOWN))
            if len(keys) > 0:
                if keys[0].key == pygame.K_f:
                    if self.player1.life < 9:
                        self.player1.life += 1
                        self.player1.stamina -= 1
                        self.player1.max_stamina -=1

                if keys[0].key == pygame.K_g:
                    if self.player1.stamina < 9:
                        self.player1.life -= 1
                        self.player1.stamina += 1
                        self.player1.max_stamina +=1

                if keys[0].key == pygame.K_h:
                    if self.player2.life < 9:
                        self.player2.life += 1
                        self.player2.stamina -= 1
                        self.player2.max_stamina -=1

                if keys[0].key == pygame.K_j:
                    if self.player2.stamina < 9:
                        self.player2.life -= 1
                        self.player2.stamina += 1
                        self.player2.max_stamina += 1
                
                if keys[0].key == pygame.K_SPACE:
                    self.menu = False
            
            self.handle_events()
            self.update_display()

    def _show_menu(self):

        self._show_lives()
        self._show_stamina()
        f = self.score_font.render('f', True, (255,255,255))
        g = self.score_font.render('g', True, (255,255,255))
        h = self.score_font.render('h', True, (255,255,255))
        j = self.score_font.render('j', True, (255,255,255))
        self.screen.blit(f, (80, 25))
        self.screen.blit(g, (80, 65))
        self.screen.blit(h, (self.screen.get_width() - 90, 25))
        self.screen.blit(j, (self.screen.get_width() - 90, 65))

        stats_text = self.over_font.render("Use keys to adjust your fighter's stats", True, (255,255,255))
        space_text = self.over_font.render('Press SPACE to start', True, (255,255,255))
        self.screen.blit(stats_text, (self.screen.get_width()*0.17, 250))
        self.screen.blit(space_text, (self.screen.get_width()*0.33, 350))

    def show_data(self):

        self._show_lives()
        self._show_stamina()

    def _show_lives(self):

        lives1 = self.score_font.render(f'{self.player1.life}', True, (255,255,255))
        lives2 = self.score_font.render(f'{self.player2.life}', True, (255,255,255))
        self.screen.blit(lives1, (50, 25))
        self.screen.blit(lives2, (self.screen.get_width() - 30, 25))
        self.screen.blit(self.blue_heart_sprite, (15, 23))
        self.screen.blit(self.red_heart_sprite, (self.screen.get_width() - 65, 23))

    def _show_stamina(self):

        stamina1 = self.score_font.render(f'{self.player1.stamina}', True, (255,255,255))
        stamina2 = self.score_font.render(f'{self.player2.stamina}', True, (255,255,255))
        self.screen.blit(stamina1, (50, 65))
        self.screen.blit(stamina2, (self.screen.get_width() - 30, 65))
        self.screen.blit(self.stamina_sprite, (0, 50))
        self.screen.blit(self.stamina_sprite, (self.screen.get_width() - 80, 50))

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

    def handle_gameover(self):

        self._check_game_over()
        self._handle_reset()

    def _check_game_over(self):
        
        if self.player1.life <= 0:

            self._show_game_over('Player 2 wins')
            self.player1.rect.y = -2000
            self.game_over = True

        if self.player2.life <= 0:

            self._show_game_over('Player 1 wins')
            self.player2.rect.y = -2000
            self.game_over = True 
    
    def _show_game_over(self, text):

        over_text = self.over_font.render(text, True, (255,255,255))
        restart_text = self.over_font.render('Press SPACE to restart', True, (255,255,255))
        reset_text = self.over_font.render('Press R to reset stats', True, (255,255,255))
        self.screen.blit(over_text, (self.screen.get_width()*0.36, 250))
        self.screen.blit(restart_text, (self.screen.get_width()*0.28, 350))
        self.screen.blit(reset_text, (self.screen.get_width()*0.3, 450))
    
    def _handle_reset(self):

        if self.game_over is True:

            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                self.game_over = False
                self._setup_elements()
            if keys[pygame.K_r]:
                self.game_over = False
                self.menu = True
                self._setup_elements()

    def handle_input(self):
        '''Handles player input from both players.'''

        keys = pygame.key.get_pressed()
        
        # player 1 movement
        if self.player1.is_ready():

            # left movement
            if keys[pygame.K_a]:
            
                if self.player1.facing_left is False:
                    self.player1.facing_left = True
                    self.player1.flip_player()

                self.player1.X_change = -self.player1.speed
                self.player1.check_dash('Left')
            
            # right movement
            if keys[pygame.K_d]:

                if self.player1.facing_left is True:
                    self.player1.facing_left = False
                    self.player1.flip_player()

                self.player1.X_change = self.player1.speed
                self.player1.check_dash('Right')
            
            if (not keys[pygame.K_a]) & (not keys[pygame.K_d]):
                self.player1.check_dash()
            
            # jumping
            if keys[pygame.K_w]:
                self.player1.deploy_jump()
            
            # sword
            if keys[pygame.K_f]:
                self.player1.deploy_strike()
            
            # shield
            if keys[pygame.K_g]:
                self.player1.deploy_shield()

            # stopping
            if keys[pygame.K_a] and keys[pygame.K_d]: 
                self.player1.X_change = 0
            if not keys[pygame.K_a] and not keys[pygame.K_d]: 
                self.player1.X_change = 0
        
        # player 2 movement
        if self.ai is True:
            keys = self.AIEnemy().ai_controls()
            
        if self.player2.is_ready():

            # left movement
            if keys[pygame.K_LEFT]:
                if self.player2.facing_left is False:
                    self.player2.facing_left = True
                    self.player2.flip_player()

                self.player2.X_change = -self.player2.speed
                self.player2.check_dash('Left')

            # right movement
            if keys[pygame.K_RIGHT]:
                if self.player2.facing_left is True:
                    self.player2.facing_left = False
                    self.player2.flip_player()

                self.player2.X_change = self.player2.speed
                self.player2.check_dash('Right')
            
            if (not keys[pygame.K_LEFT]) & (not keys[pygame.K_RIGHT]):
                self.player2.check_dash()

            # jumping
            if keys[pygame.K_UP]:
                self.player2.deploy_jump()
            
            if keys[pygame.K_h]:
                self.player2.deploy_strike()

            if keys[pygame.K_j]:
                self.player2.deploy_shield()
        
            if keys[pygame.K_RIGHT] & keys[pygame.K_LEFT]:
                self.player2.X_change = 0

            if not keys[pygame.K_RIGHT] and not keys[pygame.K_LEFT]:
                self.player2.X_change = 0

    def handle_collisions(self):
        '''Handles collisions from both players and swords.'''
        
        self._handle_sword_collisions()
        self._handle_player_collisions()

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
        
        playera.on_top = self._edge_detection(playera.rect.bottom, playerb.rect.top, 30)

        if (playera.on_top is False) & (playerb.on_top is False):
            if playera.rect.x < playerb.rect.x:
                if playera.X_change > 0:
                    playera.X_change = 0
                if playerb.X_change < 0:
                    playerb.X_change = 0
        
        # if player a is above player gb
        if playera.rect.y < playerb.rect.y:
            # player a can't fall, player b can't jump
            if playera.Y_change > 0:
                playera.Y_change = 0
            if playerb.Y_change < 0:
                playerb.Y_change = 0
    
    def _edge_detection(self,edgea,edgeb,margin=15):

        return abs(edgea - edgeb) < margin

    def _handle_sword_collisions(self):

        self._calc_sword_collisions(self.player1, self.player2)
        self._calc_sword_collisions(self.player2, self.player1)

    def _calc_sword_collisions(self,playera,playerb):
        
        if playera.sword_hurtbox is True:

            collide = bool(playera.sword_rect.colliderect(playerb.rect))
            
            if collide is True:
                
                if playera.rect.x < playerb.rect.x:
                    playerb.knockback_speed = 25
                else:
                    playerb.knockback_speed = -25

                if playerb.shield_block is False:
                    
                    if playerb.invinsible is False:    
                        playerb.deploy_knockback()
                        playerb.life -= 1
                        playerb.deploy_iframes()
                        self.sword_hit_sound.play()
            
                else:
                    if (playera.knockback is False) & (playera.stamina > 0):
                        self.sword_hit_shield_sound.play()
                        playera.stamina -= 1

                        playera.deploy_knockback()