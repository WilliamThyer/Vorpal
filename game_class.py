import pygame
import math

class Game:
        
    def __init__(self):

        pygame.init()
        self.running = True
        self.game_over = False
        self.fps = 60
        self.fps_clock = pygame.time.Clock()
        self.menu = True

        self._setup_screen()
        self._setup_elements()
        self._setup_sounds()
        self._setup_fonts()
            
    class Player(pygame.sprite.Sprite):
        
        def __init__(self, screen, fps = 120, flip=False):

            # Call the parent class (Sprite) constructor
            pygame.sprite.Sprite.__init__(self)

            self.screen = screen
            self.fps = fps

            # sprites
            self.sprite = pygame.image.load('sprites/char.png').convert()
            self.rect = self.sprite.get_rect()
            self.sword_sprite = pygame.image.load('sprites/sword.png').convert_alpha()
            self.shield_sprite = pygame.image.load('sprites/shield.png').convert_alpha()
            
            # positioning
            self.rect.x = 100
            self.rect.y = 540
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
            self.press_state = 0
            self.press_time = .1
            self.press_timer = 0
            self.dashing = False
            self.dash_mod = -1
            self.dash_time = .2
            self.dash_counter = self.dash_time*self.fps
            self.dash_speed = [0,10,20,25,25,25,25,24,24,23,21,20,19,18,17,16,15,14,13,12,11,10,10,10]

            # knockback
            self.knockback = False
            self.knockback_time = .125
            self.knockback_counter = self.knockback_time*self.fps
            self.knockback_speed = -25
            
            # sword
            self.sword_offset = 150
            self.striking = False
            self.sword_hurtbox = False
            self.sword_time = .2
            self.sword_fps_time = self.sword_time*self.fps
            self.sword_come_out_time = self.sword_fps_time - .02*self.fps
            self.sword_come_in_time = .08*self.fps

            # shield
            self.shield_offset = 80
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

            self.flip = flip
            if flip is True:
                self.sprite = pygame.transform.flip(self.sprite, True, False)
                self.sword_sprite = pygame.transform.flip(self.sword_sprite, True, False)
                self.shield_sprite = pygame.transform.flip(self.shield_sprite, True, False)
                self.rect.x = 1300
                self.sword_offset *= -1
                self.shield_offset *= -1
                self.knockback_speed *= -1
                self.dash_mod *= -1
        
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
            elif self.rect.x >= 1436:
                self.rect.x = 1436        

            if self.rect.y > 540:
                self.rect.y = 540

        def check_fall(self):

            if (self.rect.y < 540) & (self.jumping is False) & (self.on_top is False):
                self.deploy_fall()

        def deploy_fall(self):
            
            if self.falling is False:
                self.falling = True
                self.fall_ticker = 0

        def continue_fall(self):

            if (self.rect.y == 540) or (self.on_top is True):
                self.falling = False
                if self.Y_change >= 0:
                    self.Y_change = 0

            if self.falling is True:
                self.fall_ticker += 1
                self.Y_change = self.initial_fall_speed*self.fall_ticker

        def deploy_jump(self):
            
            if self.jumping is False:
                
                self.jumping = True
                self.jump_counter = self.jump_fps_time
                
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

        def check_dash(self, press):
            
            if press is True:

                # If 'back' is pressed and is wasn't previously, iterate state and start timer
                if self.press_state == 0:
                    self.press_state += 1
                    self.press_timer = self.press_time*self.fps
                
                # If 'back' if pressed after pressing and releasing before timer is up
                if self.press_state == 2:
                    if self.press_timer > 0:
                        self.deploy_dash()
                        self.press_state = 0
                        self.press_timer = 0
                    else:
                        self.press_state = 0
            
            # If 'back' is not pressed and it was previously, itererate state and timer
            if press is False:
                if self.press_state == 1:
                    self.press_state += 1

        def iterate_dash_timer(self):

            if self.press_timer > 0:
                self.press_timer -= 1

        def deploy_dash(self):

            if self.stamina > 0:
                self.X_change = self.dash_speed[0]*self.dash_mod
                self.dash_counter = self.dash_time*self.fps
                self.dashing = True

                self.stamina -= 1
                self.stamina_reload_counter = self.stamina_reload_time*self.fps
        
        def continue_dash(self):
            
            if self.dashing is True:
                if self.dash_counter <= 0:
                    self.dashing = False
                    self.X_change = 0
                else:
                    timer = int(self.dash_time*self.fps - self.dash_counter)
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

            if (self.striking is False) & (self.stamina > 0):
                self.striking = True
                self.striking_counter = self.sword_fps_time
                
                self.stamina -= 1
                self.stamina_reload_counter = self.stamina_reload_time*self.fps
                
                self.X_change = 0

        def continue_strike(self):
            '''Handles sword strike including sprite, frozen frames, and timer countdown'''

            if self.striking is True:

                self.striking_counter -= 1

                if self.sword_come_in_time < self.striking_counter < self.sword_come_out_time:
                    self.screen.blit(self.sword_sprite, (self.rect.x+self.sword_offset, self.rect.y))
                    self.sword_hurtbox = True
                else:
                    self.sword_hurtbox = False
                
                if self.striking_counter <= 0:
                    self.striking = False
        
        def deploy_shield(self):
            
            if (self.shielding is False) & (self.stamina > 0):
                self.shielding = True
                self.shield_counter = self.shield_fps_time
                
                self.stamina -= 1
                self.stamina_reload_counter = self.stamina_reload_time*self.fps
                
                self.X_change = 0
        
        def continue_shield(self):

            if self.shielding is True:

                self.shield_counter -= 1

                if self.shield_come_in_time < self.shield_counter < self.shield_come_out_time:
                    self.screen.blit(self.shield_sprite, (self.rect.x+self.shield_offset, self.rect.y))
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
            
            if self.striking or self.knockback or self.dashing or self.shielding:
                return False
            return True

    def _setup_screen(self):
        '''Creates pygame screen and draws background.'''

        self.screen = pygame.display.set_mode((1600,900))

        # title and icon
        pygame.display.set_caption('Battle')
        self.background = pygame.image.load('sprites/background.png').convert()
        self.background = pygame.transform.scale(self.background, (1600, 900))

        self.heart_sprite = pygame.image.load('sprites/heart.png').convert_alpha()
        self.heart_sprite = pygame.transform.scale(self.heart_sprite, (60, 60))
        self.stamina_sprite = pygame.image.load('sprites/stamina.png').convert_alpha()
        self.stamina_sprite = pygame.transform.scale(self.stamina_sprite, (60, 60))

    def update_display(self):
        pygame.display.update()
        self.fps_clock.tick(self.fps)

    def show_background(self):
        '''Draws background.'''

        self.screen.blit(self.background,(0,0))

    def _setup_sounds(self):
        ...
        # pygame.mixer.music.load('sprites/background.wav')
        # self.bullet_sound = pygame.mixer.Sound('sprites/laser.wav')
        # self.explosion_sound = pygame.mixer.Sound('sprites/explosion.wav')

    def _setup_elements(self):
        '''Creates character and environment elements.'''

        self.player1 = self.Player(self.screen, flip = False)
        self.player2 = self.Player(self.screen, flip = True)

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
            
            self.handle_quit()
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
        self.screen.blit(h, (1510, 25))
        self.screen.blit(j, (1510, 65))

        stats_text = self.over_font.render("Use keys to adjust your fighter's stats", True, (255,255,255))
        space_text = self.over_font.render('Press SPACE to start', True, (255,255,255))
        self.screen.blit(stats_text, (250, 250))
        self.screen.blit(space_text, (500, 350))

    def show_data(self):

        self._show_lives()
        self._show_stamina()

    def _show_lives(self):

        lives1 = self.score_font.render(f'{self.player1.life}', True, (255,255,255))
        lives2 = self.score_font.render(f'{self.player2.life}', True, (255,255,255))
        self.screen.blit(lives1, (50, 25))
        self.screen.blit(lives2, (1570, 25))
        self.screen.blit(self.heart_sprite, (0, 10))
        self.screen.blit(self.heart_sprite, (1520, 10))

    def _show_stamina(self):

        stamina1 = self.score_font.render(f'{self.player1.stamina}', True, (255,255,255))
        stamina2 = self.score_font.render(f'{self.player2.stamina}', True, (255,255,255))
        self.screen.blit(stamina1, (50, 65))
        self.screen.blit(stamina2, (1570, 65))
        self.screen.blit(self.stamina_sprite, (0, 50))
        self.screen.blit(self.stamina_sprite, (1520, 50))

    def handle_quit(self):
        '''Quits game if exit is pressed.'''

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def handle_gameover(self):

        self._check_game_over()
        self._handle_reset()

    def _check_game_over(self):
        
        if self.player1.life <= 0:

            self._show_game_over('Player 2 wins')
            self.player1.X = 2000
            self.player1.Y = 2000
            self.game_over = True

        if self.player2.life <= 0:

            self._show_game_over('Player 1 wins')
            self.player2.X = 2000
            self.player2.Y = 2000
            self.game_over = True 
    
    def _show_game_over(self, text):

        over_text = self.over_font.render(text, True, (255,255,255))
        restart_text = self.over_font.render('Press SPACE to restart', True, (255,255,255))
        reset_text = self.over_font.render('Press R to reset stats', True, (255,255,255))
        self.screen.blit(over_text, (550, 250))
        self.screen.blit(restart_text, (425, 350))
        self.screen.blit(reset_text, (450, 450))
    
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

            # back movement
            if keys[pygame.K_a]:
                self.player1.X_change = -self.player1.speed
                # back key is pressed
                self.player1.check_dash(True)
            else:
                # back key is unpressed
                self.player1.check_dash(False)

            # forward movement
            if keys[pygame.K_d]:
                self.player1.X_change = self.player1.speed
            
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
        if self.player2.is_ready():
            if keys[pygame.K_LEFT]:
                self.player2.X_change = -self.player2.speed

            if keys[pygame.K_RIGHT]:
                self.player2.X_change = self.player2.speed
                self.player2.check_dash(True)
            else:
                self.player2.check_dash(False)
            
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
            print(self.player1.X_change)
            self._calc_player_collision(self.player2, self.player1)
            print(self.player1.X_change)
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
        '''Handles sword collisions.'''
        
        # player1 striking player2
        if self.player1.sword_hurtbox is True:

            # check for collision between player1 sword and player2
            self.player1.sword_X = self.player1.rect.x + self.player1.sword_offset
            collide1 = abs(self.player1.sword_X - self.player2.rect.x)

            # if collision is touching
            if collide1 < 150:
                
                # if player2 isn't shielding
                if self.player2.shield_block is False:
                    self.player2.deploy_knockback()

                    # if player 2 isn't invinsible
                    if self.player2.invinsible is False:    
                        self.player2.life -= 1
                        self.player2.deploy_iframes()
                
                # if player2 is shielding
                else:
                    # if player1 isn't being knocked back and has stamina to lose
                    if (self.player1.knockback is False) & (self.player1.stamina > 0):
                        self.player1.stamina -= 1
                    self.player1.deploy_knockback()
        
        # player2 striking player1
        if self.player2.sword_hurtbox is True:

            self.player2.sword_X = self.player2.rect.x + self.player2.sword_offset
            collide2 = abs(self.player2.sword_X - self.player1.rect.x)

            if collide2 < 150:

                if self.player1.shield_block is False:
                    self.player1.deploy_knockback()
                
                    if self.player1.invinsible is False:
                        self.player1.life -= 1
                        self.player1.deploy_iframes()
                else:
                    if (self.player2.knockback is False) & (self.player2.stamina > 0):
                        self.player2.stamina -= 1
                    self.player2.deploy_knockback()