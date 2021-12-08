import game_class
import pygame

game = game_class.Game(ai = False)

while game.running is True:

    game.main_menu()

    game.show_background()
    
    game.handle_gameover()
    game.handle_quit()
    game.handle_input()

    game.player1.update()
    game.player2.update()

    game.handle_collisions()

    game.player1.movement()
    game.player2.movement()

    game.player1.show()
    game.player2.show()
    game.show_data()
    
    game.update_display()