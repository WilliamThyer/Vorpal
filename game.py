import game_class
import pygame

game = game_class.Game(ai = False)

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