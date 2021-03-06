from math import *
import numpy as np
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
from sources.variousFunctions import HallFunction, PrandtlFunction, machAngle
class Node:
    #On définit la classe node qui se caractérise par :
    #   la position (x,y) du noeud
    #   le flow angle theta du noeud
    #   le mach number du noeud
    #On en déduit les paramètres :
    #   le mach angle du noeud
    #   l'angle de Prandl-Meyer du noeud
    #   la valeur de K- sur le noeud
    #   la valeur de K+ sur le noeud
    def __init__(self,x,y,thet,mach,nu=False):
        self.gen_id=0
        self.node_id = 0
        self.x = x
        self.y = y
        self.thet = thet
        if nu == False :
            self.mach = mach
            self.nu = PrandtlFunction(mach)
        else :
            self.mach = HallFunction(nu)
            self.nu = nu
        self.mu = asin(1/self.mach)
        self.Km = self.thet+self.nu
        self.Kp = self.thet-self.nu
        self.CpSlope = tan(self.thet+self.mu)
        self.CmSlope = tan(self.thet-self.mu)
        if self.x == 0 :
            self.link_up = True
        else :
            self.link_up = False
        self.link_down= False
        self.temp_totale = 0
        self.p_totale = 0
        self.temp = 0
        self.p = 0
        self.attrDict ={
            "X":self.x,
            "Y":self.y,
            "thet":self.thet*(360/(2*pi)),
            "nu":self.nu*(360/(2*pi)),
            "mu":self.mu*(360/(2*pi)),
            "mach":self.mach,
            "T":self.temp,
            "P":self.p*1e-5,
        }

    def recalculate(self):
        self.mach = HallFunction(self.nu)
        self.mu = asin(1/self.mach)
        self.Km = self.thet+self.nu
        self.Kp = self.thet-self.nu
        self.CpSlope = tan(self.thet+self.mu)
        self.CmSlope = tan(self.thet-self.mu)
        self.link = False
        if self.x == 0 :
            self.link_up = True
        else :
            self.link_up = False
        self.link_down= False

    def __str__(self):
        thet = self.thet*(360/(2*pi))
        nu = self.nu*(360/(2*pi))
        mu = self.mu*(360/(2*pi))
        Km = self.Km*(360/(2*pi))
        Kp = self.Kp*(360/(2*pi))
        listing = '{:3s}{:<5.2f}'.format('X = ', self.x)
        listing += '{:3s}{:<5.2f}'.format('| Y = ',self.y)
        listing += '{:3s}{:<6.3f}'.format('| Theta = ',thet)
        listing += '{:3s}{:<6.3f}'.format('| nu = ',nu)
        listing += '{:3s}{:<6.3f}'.format('| mu = ',mu)
        listing += '{:3s}{:<5.2f}'.format('| Mach = ',self.mach)
        #listing += '{:3s}{:<5.2f}'.format('| Temp = ',self.temp)
        #listing += '{:3s}{:<5.2f}'.format('| pressure = ',self.p*1e-5)
        #optional prints
        #listing += '{:3s}{:<5.2f}'.format('| Km = ',Km)
        #listing += '{:3s}{:<5.2f}'.format('| Kp = ',Kp)
        listing += '{:3s}{:5.2f}'.format('| CpSlope = ',self.CpSlope)
        listing += '{:3s}{:5.2f}'.format('| CmSlope = ',atan(self.CmSlope)*360/(2*pi))
        return listing


    def graphNode(self,ax,style='o'):
        ax.plot(self.x,self.y,style)
        return

    def intersect(self,node,xlim,ylim):
        nu = 0.5*(node.Km - self.Kp)
        if nu < 0 : return False
        thet = 0.5*(node.Km + self.Kp)
        if nu >= 0 :
            M = HallFunction(nu)
            mu = asin(1/M)
        if self.x == node.x and self.y == node.y : return False
        if self.y ==0 : return False

        a = tan(0.5*(self.thet+thet)-0.5*(self.mu+mu))
        b = self.y - a*self.x

        c = tan(0.5*(node.thet+thet)+0.5*(node.mu+mu))
        d = node.y - c*node.x
        if a != c and b != d :
            x = (d-b)/(a-c)
            y = a*x+b
            if self.x < x < xlim and 0 < y < ylim:
                nu = 0.5*(self.Km - node.Kp)
                thet = 0.5*(self.Km + node.Kp)
                M = HallFunction(nu)
                return Node(x,y,thet,M)
        return False

    def findAxis(self,wall,xlim,ylim,limit=False):
        #Cette méthode trouve la position de l'intersection d'une caractéristique avec l'axe de la tuyère
        ywall =  wall.y + wall.c*(self.x-wall.x)
        if limit == False : limit = xlim
        if self.y > wall.y + wall.c*(self.x-wall.x):
            a = self.CmSlope
            b = self.y - a*self.x
            c = wall.c
            d = wall.y - c*wall.x
            if a != c and b != d :
                x = (d-b)/(a-c)
                y = round(a*x+b,5)
                if self.x <= x <= xlim and 0 <= y < ylim:
                    nu = self.Km
                    M = HallFunction(nu)
                    return Node(x,y,0,M)
        elif self.y < wall.y + wall.c*(self.x-wall.x):
            a = self.CpSlope
            b = self.y - a*self.x
            c = wall.c
            d = wall.y - c*wall.x
            if a != c and b != d :
                x = (d-b)/(a-c)
                y = round(a*x+b,5)
                if self.x <= x <= limit and 0 <= y <= ylim:
                    theta = atan(wall.c)
                    nu = theta - self.Kp
                    M = HallFunction(nu)
                    return Node(x,y,theta,M)
        return False



    def findContour(self,wallList) :
        #Cette méthode calcule la position de l'intersection d'une caractéristique avec le contour de la tuyère
        targetWall = wallList[-1]
        thet_intersect = self.thet
        thet_contour = targetWall.thet
        avg_slope = 0.5*( thet_contour + thet_intersect )

        a = self.CpSlope
        b = self.y - a*self.x

        c = tan(avg_slope)
        d = targetWall.y - c*targetWall.x

        if a != c and b != d :
            x = (d-b)/(a-c)
            y = a*x+b
        return Node(x,y,thet_intersect,self.mach)





    def distanceNode(self,node):
        return sqrt((self.x-node.x)**2 + (self.y-node.y)**2)

    def selectClosestNode(self,nodeList) :
        closestNode = nodeList[0]
        for node in nodeList :
            if self.distanceNode(node[0]) <= self.distanceNode(closestNode[0]) :
                closestNode = node

        return closestNode

    def compute_therm_parameters(self,temp_totale,p_totale,g):
        self.temp_totale = temp_totale
        self.p_totale = p_totale
        self.g = g
        self.temp = self.temp_totale / (1+0.5*self.mach*self.mach*(self.g-1))
        self.p = self.p_totale * pow(self.temp/self.temp_totale,self.g/(self.g-1))

        self.attrDict ={
            "X":self.x,
            "Y":self.y,
            "thet":self.thet*(360/(2*pi)),
            "nu":self.nu*(360/(2*pi)),
            "mu":self.mu*(360/(2*pi)),
            "mach":self.mach,
            "T":self.temp,
            "P":self.p*1e-5,
        }

