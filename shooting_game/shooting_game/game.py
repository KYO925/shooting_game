import pygame
import sys
import random
import os
from pygame import *
import pygame.mixer
import math

pygame.font.init()

WIDTH, HEIGHT = 600, 720
screen = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption('SHOOTER')

#イメージファイルのロード
playerimg = pygame.image.load(os.path.join('image','player.png'))
laserimg = pygame.image.load(os.path.join('image','shot.png'))
ballimg = pygame.image.load(os.path.join('image','ball.png'))
enemyimg = pygame.image.load(os.path.join('image','enemy1.png'))
enmlayimg = pygame.image.load(os.path.join('image','enemylaser.png'))
healitem = pygame.image.load(os.path.join('image','healitem.png'))
upgradeitem = pygame.image.load(os.path.join('image','upgradeitem.png'))
titlepanel = pygame.image.load(os.path.join('image','Title.png'))


#攻撃
class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, screen):
        screen.blit(self.img,(self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not(self.y <= height and self.y >= -16)

    def collision(self, obj):
        return collide(self, obj)

#特殊攻撃
class Ult:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, screen):
        screen.blit(self.img,(self.x, self.y))

    def move(self, vel):
        self.y -= 4

    def off_screen(self, height):
        return not(self.y <= height + 32 and self.y >= -32)

    def collision(self, obj):
        return collide(self, obj)

class Item:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.item_img = img
        self.mask = pygame.mask.from_surface(self.item_img)

    def draw(self, screen):
        screen.blit(self.item_img,(self.x, self.y))

    def move(self):
        self.y += 1

#プレイヤー
class Player:
    maxhealth = 100
    cooldowntime = 16
    ultcdtime = 2400
    def __init__(self, x, y, health = maxhealth):
        self.player_img = playerimg
        self.laser_img = laserimg
        self.ball_img = ballimg
        self.x = x
        self.y = y
        self.lasers = []
        self.cooldowncounter = 24
        self.ultcooldown = 0
        self.health = health
        self.mask = pygame.mask.from_surface(self.player_img)
        self.score = 0
        self.shotlock = False
        self.items = []
        self.upgrade = 0

    def draw(self, screen):
        screen.blit(self.player_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(screen)
        if self.ultcooldown != 0:
            pygame.draw.rect(screen, (200,0,0),(0,707,int(self.ultcooldown/4),15))
        else:
            pygame.draw.rect(screen,(200,200,0),(0,707,int(self.ultcdtime/4),15))
        if self.health == self.maxhealth:
            pygame.draw.rect(screen, (0,200,0),(0,692,self.health*6,15))
        elif self.health > 30:
            pygame.draw.rect(screen, (200,200,0),(0,692,self.health*6,15))
        elif self.health <= 30:
            pygame.draw.rect(screen, (200,0,0),(0,692,self.health*6,15))
        else:
            pygame.draw.rect(screen,(0,200,0),(0,692,600,15))

    def cooldown(self):
        if self.cooldowncounter >= self.cooldowntime:
            self.cooldowncounter = 0
        elif self.cooldowncounter > 0:
            self.cooldowncounter += 1
        if self.ultcooldown >= self.ultcdtime:
            self.ultcooldown = 0
        elif self.ultcooldown > 0:
            self.ultcooldown += 1

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        self.damage.play()
                        obj.health -= 10
                        if obj.health <= 0:
                            objs.remove(obj)
                            self.downsound.play()
                            self.score += obj.score
                            if obj.droprate(1):
                                item = Item(obj.x, obj.y, obj.dropitem1)
                                self.items.append(item)

                            elif obj.droprate(2):
                                item = Item(obj.x, obj.y, obj.dropitem2)
                                self.items.append(item)

                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def shot(self):
        if self.shotlock == False:
            if self.cooldowncounter == 0:
                self.shotsound.play()
                if self.upgrade == 0:
                    laser = Laser(self.x + 15, self.y, self.laser_img)
                    self.lasers.append(laser)
                if self.upgrade == 1:
                    for lasers in range(2):
                        laser = Laser(self.x + lasers*30, self.y, self.laser_img)
                        self.lasers.append(laser)
                if self.upgrade >= 2:
                    for lasers in range(3):
                        laser = Laser(self.x - 4 + lasers*19, self.y, self.laser_img)
                        self.lasers.append(laser)
                self.cooldowncounter = 1

    def ult(self):
        if self.ultcooldown == 0:
            for c in range(1):
                ult = Ult(self.x, self.y, self.ball_img)
                self.lasers.append(ult)
            self.ultcooldown = 1

#敵
class Enemy:
    cooldowntime = 12
    def __init__(self, x, y, health = 20, score = 100):
        self.enemy_img = enemyimg
        self.laser_img = enmlayimg
        self.health = health
        self.x = x
        self.y = y
        self.lasers = []
        self.cooldowncounter = 12
        self.mask = pygame.mask.from_surface(self.enemy_img)
        self.score = score
        self.dropitem1 = healitem
        self.dropitem2 = upgradeitem

    def draw(self, screen):
        screen.blit(self.enemy_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(screen)

    def move(self, vel):
        self.y += vel

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 5
                self.damage.play()
                self.lasers.remove(laser)

    def droprate(self, itemnum):
        if itemnum == 1:
            return random.randrange(32) == 0
        if itemnum == 2:
            return random.randrange(48) == 0

    def cooldown(self):
        if self.cooldowncounter >= self.cooldowntime:
            self.cooldowncounter = 0
        elif self.cooldowncounter > 0:
            self.cooldowncounter += 1

    def shot(self):
        if self.cooldowncounter == 0:
            laser = Laser(self.x + 12, self.y + 32, self.laser_img)
            self.lasers.append(laser)
            self.cooldowncounter = 1

#衝突判定
def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None

#メイン
def main():
    pygame.init()
    #サウンド
    Player.downsound = pygame.mixer.Sound(os.path.join('sound','down.WAV'))
    Player.downsound.set_volume(0.2)
    Player.shotsound = pygame.mixer.Sound(os.path.join('sound','shot3.WAV'))
    Player.shotsound.set_volume(0.1)
    Enemy.shotsound = pygame.mixer.Sound(os.path.join('sound','shot1.WAV'))
    Enemy.shotsound.set_volume(0.05)
    Enemy.damage = pygame.mixer.Sound(os.path.join('sound','damage.WAV'))
    Player.damage = pygame.mixer.Sound(os.path.join('sound','damage.WAV'))
    Enemy.damage.set_volume(0.3)
    Player.damage.set_volume(0.3)
    Item.healsound = pygame.mixer.Sound(os.path.join('sound','heal1.WAV'))
    Item.healsound.set_volume(0.2)
    Item.upgradesound = pygame.mixer.Sound(os.path.join('sound','heal2.WAV'))
    Item.upgradesound.set_volume(0.2)

    run = True
    player = Player(284, 650)
    clock = pygame.time.Clock()
    player_v = 3
    laser_v = 10
    FPS = 120
    enemies = []
    enemy_v = 1
    enemylaser_v = 5
    clocktimer = FPS
    losttime = 0
    lost = False
    font1 = pygame.font.SysFont(None, 24)
    level = 0

    #描画
    def draw_window():
        screen.fill((0, 0, 0))

        for item in player.items:
            item.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        player.draw(screen)

        scoreboard = font1.render(f'SCORE  {player.score}', True, (200,200,200))
        levelcount = font1.render(f'LEVEL   {level}', True, (200,200,200))
        screen.blit(scoreboard, (0,0))
        screen.blit(levelcount, (0,16))
        pygame.display.update()

    def game_over(score, level):
        gameoverfont = pygame.font.SysFont(None, 32)
        run = True
        while run:
            screen.fill((0,0,0))
            gameovertext = gameoverfont.render('GAME OVER', True, (200,50,50))
            scoreboard = gameoverfont.render(f'SCORE  {score}', True, (200,200,0))
            levelcount = gameoverfont.render(f'LEVEL   {level}', True, (200,200,0))
            screen.blit(gameovertext, (int(WIDTH/2) - int(gameovertext.get_width()/2),300))
            screen.blit(scoreboard, (int(WIDTH/2) - int(scoreboard.get_width()/2),350))
            screen.blit(levelcount, (int(WIDTH/2) - int(levelcount.get_width()/2),400))
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif event.key == K_SPACE:
                        run = False

    #ループ
    while run:
        clock.tick(FPS)
        draw_window()

        if player.health <= 0:
            player.shotlock = True
            game_over(player.score, level)
            run = False

        #時間
        if FPS > clocktimer > 0:
            clocktimer += 1
        elif clocktimer == FPS:
            clocktimer = 1

        #敵の生成
        if len(enemies) == 0:
            level += 1
            for i in range(level*10):
                if i % 2 == 0:
                    enemy = Enemy(random.randrange(24, WIDTH - 56), random.randrange(-1000, -100))
                    enemies.append(enemy)

        #操作の検知
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player.x - player_v > 0:
            player.x -= player_v
        if keys[pygame.K_d] and player.x + player_v + playerimg.get_width() < WIDTH:
            player.x += player_v
        if keys[pygame.K_w] and player.y - player_v > 0:
            player.y -= player_v
        if keys[pygame.K_s] and player.y + player_v + playerimg.get_height() + 32 < HEIGHT:
            player.y += player_v
        if keys[pygame.K_SPACE]:
            player.shot()
        if keys[pygame.K_b]:
            player.ult()

        for event in pygame.event.get():
            #終了ボタン
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    run = False
                #減速
                if event.key == K_v:
                    if player_v == 3:
                        player_v = 2
                    elif player_v == 2:
                        player_v = 3

        #敵や攻撃の移動
        for enemy in enemies:
            enemy.move_lasers(enemylaser_v, player)

            if clocktimer % 2 == 0:
                enemy.move(enemy_v)

            if enemy.y + enemyimg.get_height() > 0 and random.randrange(0, FPS*2) == 1:
                enemy.shot()
                Enemy.shotsound.play()

            if enemy.y + enemyimg.get_height() > HEIGHT + 32:
                player.health -= 5
                enemies.remove(enemy)

            if collide(enemy, player):
                player.health -= 10
                Player.downsound.play()
                enemies.remove(enemy)

        for item in player.items:
            item.move()

            if collide(item, player):
                if item.item_img == healitem:
                    Item.healsound.play()
                    player.items.remove(item)
                    player.score += 300
                    if player.health + 10 < player.maxhealth:
                        player.health += 10
                    elif player.health < player.maxhealth:
                        player.health = player.maxhealth

                if item.item_img == upgradeitem:
                    Item.upgradesound.play()
                    player.items.remove(item)
                    player.score += 1000
                    player.upgrade += 1

            if item.y + healitem.get_height() > HEIGHT + 32:
                player.items.remove(item)

        player.move_lasers(-laser_v, enemies)


def main_menu():
    titlefont = pygame.font.SysFont(None, 32)
    run = True
    while True:
        screen.fill((0,0,0))
        screen.blit(titlepanel, (int(WIDTH/2) -int(titlepanel.get_width()/2),200))
        titletext = titlefont.render('PRESS SPACE TO START', True, (200,200,0))
        screen.blit(titletext, (int(WIDTH/2) -int(titletext.get_width()/2),400))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_SPACE:
                    main()


main_menu()
