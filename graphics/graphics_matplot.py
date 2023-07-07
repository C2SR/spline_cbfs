import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as anim
from matplotlib.patches import Rectangle


class Plot2DSimulation():

    def __init__(self, robots, paths, barriers, logs, **kwargs):
        '''
        Initializes graphical objects.
        '''        
        plot_config = {
            "axeslim": (-6,6,-6,6),
            "path_length": 40, 
            "numpoints": 80
        }
        if "plot_config" in kwargs.keys():
            plot_config = kwargs["plot_config"]

        self.colors = [ 'c', 'm', 'g' ]
        self.robots = robots
        self.paths = paths
        self.barriers = barriers

        self.num_robots = len(self.robots)
        self.num_paths = len(self.paths)
        self.num_barriers = len(self.barriers)
        
        # Initialize plot objects
        self.fig, self.ax = plt.subplots()
        self.ax.set_title('Traffic Control with CLF-CBFs')

        self.ax_lims = plot_config["axeslim"][0:2]
        self.ax.set_xlim( plot_config["axeslim"][0:2] )
        self.ax.set_ylim( plot_config["axeslim"][2:4] )
        self.ax.set_aspect('equal', adjustable='box')

        # Get logs
        self.sample_time = logs["sample_time"]
        self.time = logs["time"]
        self.robot_logs = logs["robots"]
        self.gamma_logs = logs["gamma"]
        self.gamma_barrier_logs = logs["gamma_barriers"]

        self.num_steps = len(self.time)

        # Get point resolution for graphical objects
        self.path_length = plot_config["path_length"]
        self.numpoints = plot_config["numpoints"]

        # Initalize graphical objects
        self.time_text = self.ax.text(plot_config["axeslim"][1]-10, plot_config["axeslim"][3]-3, str("Time = "))

        self.robot_positions, self.robot_trajectories, self.robot_geometries, self.robot_ellipses, self.virtual_pts, self.arrows = [], [], [], [], [], []
        for k in range(self.num_robots):
            robot_pos, = self.ax.plot([],[],lw=1,color='black',marker='o',markersize=4.0)
            self.robot_positions.append(robot_pos)

            ellipse, = self.ax.plot([],[],lw=1,color='blue')
            self.robot_ellipses.append(ellipse)

            virtual_pt,  = self.ax.plot([],[],lw=1,color='red',marker='o',markersize=4.0)
            self.virtual_pts.append(virtual_pt)

            robot_traj, = self.ax.plot([],[],lw=2,color=self.colors[k])
            
            robot_x, robot_y, robot_angle = self.robot_logs[k][0][0], self.robot_logs[k][1][0], self.robot_logs[k][2][0]
            # pose = (robot_x, robot_y, robot_angle)
            center = self.robots[k].geometry.get_center( (robot_x, robot_y, robot_angle) )
            robot_geometry = Rectangle( center,
                                       width=self.robots[k].geometry.length,
                                       height=self.robots[k].geometry.width, 
                                       angle=np.rad2deg(robot_angle), rotation_point="xy" )

            self.robot_trajectories.append( robot_traj )
            self.robot_geometries.append( robot_geometry )
            # self.circles.append( plt.Circle((robot_x, robot_y), plot_config["radius"], color=self.colors[k], linestyle = '--', fill=False) )

        self.path_graphs = []
        for k in range(self.num_paths):
            i_graph, = self.ax.plot([],[], linestyle='dashed', lw=0.8, alpha=0.8, color=self.colors[k])
            self.path_graphs.append( i_graph )

        self.barrier_graphs = []
        for k in range(self.num_barriers):
            i_graph, = self.ax.plot([],[], lw=1.5, alpha=1.0, color='r')
            i_arrow, = self.ax.plot([],[], linestyle='dashed', lw=1.5, alpha=1.0, color='r')
            self.barrier_graphs.append( i_graph )
            self.arrows.append([])
            for _ in range(self.num_robots):
                self.arrows[-1].append( i_arrow )

        self.animation = None

    def init(self):
        '''
        Initialization function for the animation.
        '''
        self.time_text.text = str("Time = ")

        for i in range(self.num_robots):
            self.robot_positions[i].set_data([],[])
            self.robot_trajectories[i].set_data([],[])
            self.robot_ellipses[i].set_data([],[])

        for i in range(self.num_paths):
            xpath, ypath = [], []
            for k in range(self.numpoints):
                gamma = k*self.path_length/self.numpoints
                # self.paths[i].set_path_state(gamma)
                pos = self.paths[i].get_path_point(gamma)
                xpath.append(pos[0])
                ypath.append(pos[1])
            self.path_graphs[i].set_data(xpath, ypath)
            self.virtual_pts[i].set_data([],[])

        for i in range(self.num_barriers):
            xpath, ypath = [], []
            for k in range(self.numpoints):
                gamma = k*self.path_length/self.numpoints
                # self.paths[i].set_path_state(gamma)
                if gamma <= self.barriers[i].gamma_max:
                    pos = self.barriers[i].get_path_point(gamma)
                    xpath.append(pos[0])
                    ypath.append(pos[1])
                else: break
            self.barrier_graphs[i].set_data(xpath, ypath)

        graphical_elements = self.robot_positions + self.robot_trajectories + self.path_graphs + self.barrier_graphs + self.virtual_pts
        graphical_elements.append(self.time_text)
        for k in range(self.num_barriers):
            graphical_elements += self.arrows[k]
        
        return graphical_elements

    def update(self, i):
        '''
        Update function for the animation.
        '''
        # Update simulation time graphics
        current_time = np.around(self.time[i], decimals = 2)
        self.time_text.set_text("Time = " + str(current_time) + "s")

        # Update robot graphics
        for k in range(self.num_robots):
            self.robot_positions[k].set_data(self.robot_logs[k][0][i], self.robot_logs[k][1][i])

            xdata, ydata = self.robot_logs[k][0][0:i], self.robot_logs[k][1][0:i]
            self.robot_trajectories[k].set_data(xdata, ydata)

            robot_x, robot_y, robot_angle = self.robot_logs[k][0][i], self.robot_logs[k][1][i], self.robot_logs[k][2][i]
            pose = (robot_x, robot_y, robot_angle)
            self.robot_geometries[k].xy = self.robots[k].geometry.get_corners(pose, "bottomleft")
            self.robot_geometries[k].angle = np.rad2deg(robot_angle)

            self.ax.add_patch(self.robot_geometries[k])

            center_pose = np.hstack([ self.robots[k].geometry.get_center(pose), robot_angle ])
            self.robots[k].barrier.update_pose( center_pose )
            self.robots[k].barrier.contour_plot(self.robot_ellipses[k])

        # Update path graphics
        for k in range(self.num_paths):

            # self.paths[k].set_path_state(self.gamma_logs[k][i])
            gamma = self.gamma_logs[k][i]
            pos = self.paths[k].get_path_point(gamma)

            self.virtual_pts[k].set_data(pos[0], pos[1])

        # Update barrier graphics (arrows)
        for k in range(self.num_barriers):

            gamma = self.gamma_barrier_logs[k][i]
            # pos = self.barriers[k].get_path_point(gamma)
            normal = self.barriers[k].get_path_normal(gamma)

            self.barriers[k].set_path_state(gamma)
            for j in range(self.num_robots):
                _, _, spline_pt = self.barriers[k].compute_barrier( self.robots[j].barrier )
                self.arrows[k][j].set_data([ spline_pt[0], spline_pt[0] + normal[0]], [ spline_pt[1], spline_pt[1] + normal[1]])

        # Add artists
        graphical_elements = self.robot_positions + self.robot_trajectories + self.robot_geometries + self.path_graphs + self.barrier_graphs + self.virtual_pts
        graphical_elements.append(self.time_text)
        graphical_elements += self.robot_ellipses
        for k in range(self.num_barriers):
            graphical_elements += self.arrows[k]

        return graphical_elements

    def animate(self):
        '''
        Show animation.
        '''
        self.animation = anim.FuncAnimation(self.fig, func=self.update, init_func=self.init, frames=self.num_steps, interval=20, repeat=False, blit=True)
        plt.show()

    def get_frame(self, t):
        '''
        Updates frame at time time.
        '''
        self.init()
        step = int(np.floor(t/self.sample_time))
        graphical_elements = self.update(step)

        return graphical_elements

    def plot_frame(self, t):
        '''
        Plots specific animation frame at time t.
        '''
        self.get_frame(t)
        plt.show()