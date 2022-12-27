import pygame
from pygame.locals import *
from pygame import mixer
import pickle
from os import path
from classes.Enemy import Enemy
from classes.Button import Button
from classes.Lava import Lava
from classes.Coin import Coin
from classes.Platform import Platform
from classes.Exit import Exit
from classes.variaveis_globais import variaveis

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = variaveis.screen_width
screen_height = variaveis.screen_height
screen = variaveis.screen
tile_size= variaveis.tile_size
pygame.display.set_caption('Joint Journey')

#define font
font = pygame.font.SysFont('Bauhaus 93', 50)
font_score = pygame.font.SysFont('Bauhaus 93', 15)

#define game variables

game_over = 0
game_over_P1 = False
game_over_P2 = False
main_menu = True
level=1
max_levels=2
score=0

#define colours
white = (255, 255, 255)



#load images
sun_img = pygame.image.load('img/sun.png')
bg_img = pygame.image.load('img/bg.jpg')
restart_img = pygame.image.load('img/restart_btn.png')
start_img = pygame.image.load('img/start_btn.png')
exit_img = pygame.image.load('img/exit_btn.png')

#load sounds
pygame.mixer.music.load('img/music.wav')
pygame.mixer.music.play(-1, 0.0, 5000)
coin_fx = pygame.mixer.Sound('img/coin.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('img/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('img/game_over.wav')
game_over_fx.set_volume(0.5)


def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))
#function to reset level
def reset_level(level):
	player.reset(30, screen_height - 100)
	player2.reset(450, screen_height - 100)
	blob_group.empty()
	platform_group.empty()
	lava_group.empty()
	exit_group.empty()
	
	#load in level data and create world
	if path.exists(f'level{level}_data'):
		pickle_in = open(f'level{level}_data', 'rb')
		world_data = pickle.load(pickle_in)
	world = World(world_data)

	return world




class Player():
	def __init__(self, x, y):
		self.reset(x, y)


	def update(self, game_over, game_over_P1, game_over_P2 ):
		dx=0
		dy=0
		walk_cooldown = 5
		col_thresh = 20
		if game_over == 0:
			key=pygame.key.get_pressed()
			if key[pygame.K_UP] and self.jumped == False and self.in_air == False:
				jump_fx.play()
				self.vel_y = -11
				self.jumped = True
			if key[pygame.K_UP] == False:
				self.jumped = False
			if key[pygame.K_LEFT]==True:
				dx-=2
				self.counter += 1
				self.direction = -1
			if key[pygame.K_RIGHT]==True:
				dx+=2
				self.counter += 1
				self.direction = 1
			if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
				self.counter = 0
				self.index = 0
				if self.direction == 1:
					self.image = self.images_right[self.index]
				if self.direction == -1:
					self.image = self.images_left[self.index]

			if self.counter > walk_cooldown:
				self.counter = 0	
				self.index += 1
				if self.index >= len(self.images_right):
					self.index = 0
				if self.direction == 1:
					self.image = self.images_right[self.index]
				if self.direction == -1:
					self.image = self.images_left[self.index]

			self.vel_y += 1
			if self.vel_y > 10:
				self.vel_y = 10
			dy += self.vel_y

			
			#check for collision
			self.in_air = True
			for tile in world.tile_list:
				#check for collision in x direction
				if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
					dx = 0
				#check for collision in y direction
				if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
					#check if below the ground i.e. jumping
					if self.vel_y < 0:
						dy = tile[1].bottom - self.rect.top
						self.vel_y = 0
					#check if above the ground i.e. falling
					elif self.vel_y >= 0:
						dy = tile[1].top - self.rect.bottom
						self.vel_y = 0
						self.in_air = False


			#check for collision with enemies
			if pygame.sprite.spritecollide(self, blob_group, False):
				game_over = -1
				game_over_fx.play()
			#check for collision with lava
			if pygame.sprite.spritecollide(self, lava_group, False):
				game_over = -1
				game_over_fx.play()
			#check for collision with exit
			if pygame.sprite.spritecollide(self, exit_group, False):
				game_over_P1 = True
				if game_over_P2:
					game_over = 1
			#check for collision with platforms
			for platform in platform_group:
				#collision in the x direction
				if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
					dx = 0
				#collision in the y direction
				if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
					#check if below platform
					if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
						self.vel_y = 0
						dy = platform.rect.bottom - self.rect.top
					#check if above platform
					elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
						self.rect.bottom = platform.rect.top - 1
						self.in_air = False
						dy = 0
					#move sideways with the platform
					if platform.move_x != 0:
						self.rect.x += platform.move_direction

			self.rect.x+=dx
			self.rect.y+=dy

			
		elif game_over == -1:
			self.image = self.dead_image
			draw_text('Você Perdeu!', font, white, (screen_width // 2) - 150, screen_height // 2)
			if self.rect.y > 200:
				self.rect.y -= 5

		screen.blit(self.image, self.rect)
		

		return game_over, game_over_P1, game_over_P2

	def reset(self, x, y):
		self.images_right = []
		self.images_left = []
		self.index = 0
		self.counter = 0
		for num in range(1, 5):
			img_right = pygame.image.load(f'img/guy{num}.png')
			img_right = pygame.transform.scale(img_right, (20, 40))
			img_left = pygame.transform.flip(img_right, True, False)
			self.images_right.append(img_right)
			self.images_left.append(img_left)
		self.dead_image = pygame.image.load('img/ghost.png')
		self.image = self.images_right[self.index]
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.vel_y = 0
		self.jumped = False
		self.direction = 0
		self.in_air = True

class Player2():
	def __init__(self, x, y):
		self.reset(x, y)


	def update(self, game_over, game_over_P1, game_over_P2 ):
		dx=0
		dy=0
		walk_cooldown = 5
		col_thresh = 20
		if game_over == 0:
			key=pygame.key.get_pressed()
			if key[pygame.K_w] and self.jumped == False and self.in_air == False:
				jump_fx.play()
				self.vel_y = -11
				self.jumped = True
			if key[pygame.K_w] == False:
				self.jumped = False
			if key[pygame.K_a]==True:
				dx-=2
				self.counter += 1
				self.direction = -1
			if key[pygame.K_d]==True:
				dx+=2
				self.counter += 1
				self.direction = 1
			if key[pygame.K_a] == False and key[pygame.K_d] == False:
				self.counter = 0
				self.index = 0
				if self.direction == 1:
					self.image = self.images_right[self.index]
				if self.direction == -1:
					self.image = self.images_left[self.index]

			if self.counter > walk_cooldown:
				self.counter = 0	
				self.index += 1
				if self.index >= len(self.images_right):
					self.index = 0
				if self.direction == 1:
					self.image = self.images_right[self.index]
				if self.direction == -1:
					self.image = self.images_left[self.index]

			self.vel_y += 1
			if self.vel_y > 10:
				self.vel_y = 10
			dy += self.vel_y

			
			#check for collision
			self.in_air = True
			for tile in world.tile_list:
				#check for collision in x direction
				if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
					dx = 0
				#check for collision in y direction
				if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
					#check if below the ground i.e. jumping
					if self.vel_y < 0:
						dy = tile[1].bottom - self.rect.top
						self.vel_y = 0
					#check if above the ground i.e. falling
					elif self.vel_y >= 0:
						dy = tile[1].top - self.rect.bottom
						self.vel_y = 0
						self.in_air = False


			#check for collision with enemies
			if pygame.sprite.spritecollide(self, blob_group, False):
				game_over = -1
				game_over_fx.play()
			#check for collision with lava
			if pygame.sprite.spritecollide(self, lava_group, False):
				game_over = -1
				game_over_fx.play()
			#check for collision with exit
			if pygame.sprite.spritecollide(self, exit_group, False):
				game_over_P2 = True
				if game_over_P1:
					game_over = 1
			#check for collision with platforms
			for platform in platform_group:
				#collision in the x direction
				if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
					dx = 0
				#collision in the y direction
				if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
					#check if below platform
					if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
						self.vel_y = 0
						dy = platform.rect.bottom - self.rect.top
					#check if above platform
					elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
						self.rect.bottom = platform.rect.top - 1
						self.in_air = False
						dy = 0
					#move sideways with the platform
					if platform.move_x != 0:
						self.rect.x += platform.move_direction

			self.rect.x+=dx
			self.rect.y+=dy

			
		elif game_over == -1:
			self.image = self.dead_image
			draw_text('Você Perdeu!', font, white, (screen_width // 2) - 150, screen_height // 2)
			if self.rect.y > 200:
				self.rect.y -= 5

		screen.blit(self.image, self.rect)
		

		return game_over, game_over_P1, game_over_P2

	def reset(self, x, y):
		self.images_right = []
		self.images_left = []
		self.index = 0
		self.counter = 0
		for num in range(1, 5):
			img_right = pygame.image.load(f'img/boy{num}.png')
			img_right = pygame.transform.scale(img_right, (20, 40))
			img_left = pygame.transform.flip(img_right, True, False)
			self.images_right.append(img_right)
			self.images_left.append(img_left)
		self.dead_image = pygame.image.load('img/ghost.png')
		self.image = self.images_left[self.index]
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.vel_y = 0
		self.jumped = False
		self.direction = 0
		self.in_air = True


class World():
	def __init__(self, data):
		self.tile_list = []

		#load images
		dirt_img = pygame.image.load('img/dirt.png')
		pedra_img = pygame.image.load('img/pedra.png')

		row_count = 0
		for row in data:
			col_count = 0
			for tile in row:
				if tile == 1:
					img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
					img_rect = img.get_rect()
					img_rect.x = col_count * tile_size
					img_rect.y = row_count * tile_size
					tile = (img, img_rect)
					self.tile_list.append(tile)
				if tile == 2:
					img = pygame.transform.scale(pedra_img, (tile_size, tile_size))
					img_rect = img.get_rect()
					img_rect.x = col_count * tile_size
					img_rect.y = row_count * tile_size
					tile = (img, img_rect)
					self.tile_list.append(tile)
				if tile == 3:
					blob = Enemy(col_count * tile_size, row_count * tile_size+10)
					blob_group.add(blob)
				if tile == 4:
					platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
					platform_group.add(platform)
				if tile == 5:
					platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
					platform_group.add(platform)
				if tile == 6:
					lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
					lava_group.add(lava)
				if tile == 7:
					coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
					coin_group.add(coin)
				if tile == 8:
					exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
					exit_group.add(exit)
				col_count += 1
			row_count += 1

	def draw(self):
		for tile in self.tile_list:
			screen.blit(tile[0], tile[1])


player = Player(30, screen_height-80)
player2 = Player2(450, screen_height-80)

blob_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

score_coin = Coin(tile_size // 2, tile_size // 2)
coin_group.add(score_coin)

if path.exists(f'level{level}_data'):
	pickle_in = open(f'level{level}_data', 'rb')
	world_data = pickle.load(pickle_in)
world = World(world_data)

restart_button = Button(screen_width // 2-45, screen_height // 2 + 50, restart_img)
start_button = Button(screen_width // 2 - 175, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + 75, screen_height // 2, exit_img)

run = True
while run:

	clock.tick(fps)

	screen.blit(bg_img, (0, 0))
	screen.blit(sun_img, (100, 100))

	if main_menu == True:
		if exit_button.draw():
			run = False
		if start_button.draw():
			main_menu = False
	else: 
		world.draw()

		if game_over == 0:
			blob_group.update()
			platform_group.update()
			if pygame.sprite.spritecollide(player, coin_group, True) or pygame.sprite.spritecollide(player2, coin_group, True):
				score += 1
				coin_fx.play()
			draw_text('X ' + str(score), font_score, white, tile_size - 5, 5)
		blob_group.update()

		blob_group.draw(screen)
		platform_group.draw(screen)
		lava_group.draw(screen)
		coin_group.draw(screen)
		exit_group.draw(screen)

		game_over, game_over_P1, game_over_P2 = player.update(game_over, game_over_P1, game_over_P2)
		game_over, game_over_P1, game_over_P2 = player2.update(game_over, game_over_P1, game_over_P2)
		
	
		#if player has died
		if game_over == -1:
			if restart_button.draw():
				world_data = []
				world = reset_level(level)
				game_over = 0
				score=0
				game_over_P1 = False
				game_over_P2 = False
		#if player has completed the level
		if game_over == 1:
			#reset game and go to next level
			level += 1
			if level <= max_levels:
				#reset level
				world_data = []
				world = reset_level(level)
				game_over = 0
				game_over_P1 = False
				game_over_P2 = False
			else:
				draw_text('Você Ganhou!', font, white, (screen_width // 2)-150, screen_height // 2)
				if restart_button.draw():
					level = 1
					#reset level
					world_data = []
					world = reset_level(level)
					game_over = 0
					score=0
					game_over_P1 = False
					game_over_P2 = False
	for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False

	pygame.display.update()

pygame.quit()