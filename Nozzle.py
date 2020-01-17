from math import *
import numpy as np
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
from variousFunctions import *
from Node import *
from Segment import *
from Wall import *
import csv
from CoolProp.CoolProp import PropsSI
class Nozzle :

    def __init__(self,
                 ntype,
                 tank_pressure,
                 tank_temperature,
                 air_gas_constant,
                 mass_flow,
                 g,
                 theta_top,
                 theta_step_num,
                 theta_bottom=0.1):
        self.tank_pressure    = tank_pressure
        self.tank_temperature = tank_temperature
        self.throat_mach        = 1
        self.air_gas_constant   = air_gas_constant
        self.mass_flow          = mass_flow
        self.g                  = g
        self.theta_step_num     = theta_step_num
        self.theta_top          = theta_top
        self.theta_bottom       = theta_bottom
        self.ntype = ntype

        if self.ntype == 'min' :
            self.initialize()

        if self.ntype == 'expansion' :
            self.initialize()

        self.compute()
####################     Computing    ######################
    def compute(self):
        seg = []
        wall_seg = []
        gen = []
        gen.append(self.seed.copy())
        new_gen=[]
        new_gen.append(gen[0][0].interWall(self.floor,self.xlim,self.ylim))
        seg.append(Segment(gen[0][0],new_gen[-1]))
        for node in gen[0][1:]:
            new_gen.append(node.interKm(new_gen[-1],self.xlim,self.ylim))
            seg.append(Segment(node,new_gen[-1]))
            seg.append(Segment(new_gen[-1],new_gen[-2]))
        gen.append(new_gen.copy())
        for i in range(1,self.theta_step_num):
            new_gen=[]
            new_gen.append(gen[i][1].interWall(self.floor,self.xlim,self.ylim))
            seg.append(Segment(gen[i][1],new_gen[-1]))
            for node in gen[i][2:]:
                new_gen.append(node.interKm(new_gen[-1],self.xlim,self.ylim))
                seg.append(Segment(node,new_gen[-1]))
                seg.append(Segment(new_gen[-1],new_gen[-2]))
            gen.append(new_gen.copy())
        for generation in gen[1:] :
            last_node = generation[-1]
            wall_candidate = last_node.findRoof(self.wall)
            self.wall.append(wall_candidate)
            wall_seg.append(Segment(self.wall[-1],self.wall[-2]))
            seg.append(Segment(self.wall[-1],last_node))
        self.gen=gen
        self.seg=seg
        self.wall_seg=wall_seg


    def initialize(self) :
        if self.ntype=='expansion' :
            #Calculating the throat's area and radius
            rho=PropsSI("D","P",self.tank_pressure,"T",self.tank_temperature,"Air")
            throat_surf = self.mass_flow/(rho*sqrt(self.g*self.air_gas_constant*self.tank_temperature))
            self.throat_radius =sqrt(throat_surf/pi)
            #Calculating total temp and pressure from (T/P) at the throat

            self.temp_totale = self.tank_temperature*(1+(self.g-1)*0.5*0)
            self.p_totale = self.tank_pressure*pow((1+(self.g-1)*0.5*0*0),self.g/(self.g-1))
            theta = np.linspace(-pi/2, 1.5*pi, 1000)
            y0 = self.throat_radius
            x1 = 1.0*y0
            self.theta_top = self.theta_top*2*pi/360
            r=x1/sin(self.theta_top)
            y1=r+y0-r*cos(self.theta_top)
            x_circle = 0
            y_circle = y0+r
            x=r*np.cos(theta)+x_circle
            y = r*np.sin(theta)+y_circle
            val = [[x[i],y[i]] for i in range(len(x)) if 0<=x[i]<=x1 and y[i]<=y1]
            valbis = [[x[i],y[i]] for i in range(len(x)) if 0>=x[i] or x[i]>=x1 or y[i]>=y1]
            xbis = [i[0] for i in valbis]
            ybis = [i[1] for i in valbis]
            x = [i[0] for i in val]
            y = [i[1] for i in val]
            x_seed = np.linspace(x1/25,x1,10)
            theta_seed = [asin(i/r) for i in x_seed]
            y_seed = [r+y0-r*cos(i) for i in theta_seed]
            nu_seed = theta_seed.copy()
            mach_seed = [m_from_nu(i) for i in nu_seed]
            self.seed = [Node(x_seed[i],y_seed[i],theta_seed[i],mach_seed[i],nu_seed[i]) for i in range(len(x_seed))]
            self.floor = Wall(0,0,0)
            self.wall = self.seed.copy()
            self.xlim = 10*self.throat_radius
            self.ylim = 10*self.throat_radius

        if self.ntype=='min':
            rho=PropsSI("D","P",self.tank_pressure,"T",self.tank_temperature,"Air")
            throat_surf = self.mass_flow/(rho*sqrt(self.g*self.air_gas_constant*self.tank_temperature))
            self.throat_radius =sqrt(throat_surf/pi)
            #Calculating total temp and pressure from (T/P) at the throat
            self.temp_totale = self.tank_temperature*(1+(self.g-1)*0.5*self.throat_mach*self.throat_mach)
            self.p_totale = self.tank_pressure*pow((1+(self.g-1)*0.5*self.throat_mach*self.throat_mach),self.g/(self.g-1))
            #Defining the angles with which to start the calculation
            self.theta_list = np.linspace(self.theta_bottom,self.theta_top,self.theta_step_num)
            self.theta_list = [i * 2 * pi / (360) for i in  self.theta_list]
            #Creating intial angles at sharp throat
            self.seed = [ Node(0,self.throat_radius,i,1,nu=i) for i in self.theta_list ]
            self.floor = Wall(0,0,0)
            self.wall = [self.seed[-1]]
            self.xlim = 10*self.throat_radius
            self.ylim = 10*self.throat_radius

    def results(self) :
        return
    def graph(self,show_seg=True):
            plt.figure()
            nozzle_ax = plt.subplot(111)
            nozzle_ax.plot([i.x for i in self.wall],[i.y for i in self.wall],'b-')
            # nozzle_ax.plot([i.x for i in self.wall],[-i.y for i in self.wall],'b-')
            if show_seg :
                for i in self.seg :
                    i.graphSegment(nozzle_ax)
            nozzle_ax.plot([0,self.wall[-1].x],[0,0],'k:')

            nozzle_ax.set_aspect('equal')
            nozzle_ax.grid()
            plt.show()

    def Printseed(self):
        print('{:^75s}'.format('******Initial points******'))
        for i in self.seed:
            print(i)

    def save_contour(self,result_path='results/',catia=False):
        if catia :
            with open(result_path+'contour_catia.csv', mode='w',newline='') as csv_file:
                fieldnames = ['X','Y','Z']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=";")

                # writer.writeheader()
                writer.writerow({'X':'StartLoft','Y':'','Z':''})
                writer.writerow({'X':'StartCurve','Y':'','Z':''})
                for i in self.wall :
                    writer.writerow({'X': str(i.x).replace('.',','), 'Y': str(i.y).replace('.',','),'Z':'0'})
                writer.writerow({'X':'EndCurve','Y':'','Z':''})
                writer.writerow({'X':'EndLoft','Y':'','Z':''})
                writer.writerow({'X':'End','Y':'','Z':''})
        else :
            with open(result_path+'contour.csv', mode='w',newline='') as csv_file:
                fieldnames = ['X','Y']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=";")

                writer.writeheader()
                for i in self.wall :
                    writer.writerow({'X': str(i.x).replace('.',','), 'Y': str(i.y).replace('.',',')})

    def save_data(self,selection=[],result_path='results/'):
        with open(result_path+'nodes.csv', mode='w',newline='') as csv_file:
            fieldnames = ['']+selection
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            writer.writerow({'':'SEED'})
            for node in self.seed :
                dict = {'':''}
                for prop in selection :
                    dict[prop] = str(node.attrDict[prop]).replace('.',',')
                writer.writerow(dict)
            writer.writerow({'':'FAN'})
            for node in self.fan :
                dict = {'':''}
                for prop in selection :
                    dict[prop] = str(node.attrDict[prop]).replace('.',',')
                writer.writerow(dict)
            writer.writerow({'':'CONTOUR'})
            for node in self.wall :
                dict = {'':''}
                for prop in selection :
                    dict[prop] = str(node.attrDict[prop]).replace('.',',')
                writer.writerow(dict)

    def misc(self):
        return
