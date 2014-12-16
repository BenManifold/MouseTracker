#!/usr/local/bin/sage
from mouseAux import *
from matplotlib import *
from sage.plot.text import *
import math
#import numpy as np


CURRENT_VERSION = 6.05

class tracker:
    '''Tracking class for parsing, analyzing, and displaying data collected from automated video surveillance using openCV.\n
        Available methods:\n

        load(filename = "")
        save()
        drawTracks(joined = True, color_method = "IMPORTANCE", min_time = 15)
        drawSizeDistribution()
        getObjectTimes(min_size, max_size, min_length)
        setJoinConstants( TIMEC, SPACEC, SPEEDC, SIZEC )
    '''
    __filename__ = ''
    __data__ = {}
    __FPS__ = 29.97
    __MAX_INACTIVE_FRAMES__ = 1
    __TIMEC__  = .35
    __SPACEC__ = .35
    __SPEEDC__ = .15
    __SIZEC__  = .15
    __SMALL_SIZE_LB__ = 25
    __MID_SIZE_UB__ = 350
    __SLOW_SPEED_UB__ = 3
    __DATA_VERSION__ = 0
    
    ########################################################################################################
    def __init__(self, *arguments, **keywords):
        '''Initialize instance of a tracker. First argument should be filename. Available keyword parameters: filename = "file".'''
        if keywords:
            self.__filename__ = keywords.get('filename')
            if not self.__filename__:
                print "Invalid filename. Please enter a valid filename",

            rebuild = keywords.get('rebuild')
            if rebuild:
                self.load(filename = self.__filename__, rebuild = true)

            else:
			    self.load(filename = self.__filename__)
                
            if 'smallupperbound' in keywords:
                self.__SMALL_SIZE_UB__ = keywords.get('smallupperbound')
            else: 
                self.__SMALL_SIZE_UB__ = 175   
        elif arguments[0]:
            self.__filename__ = arguments[0]

            self.load( filename = self.__filename__ )
    ########################################################################################################
    def __parseRawData__(self):
        '''Generate python dictionary out of plain text openCV output.'''
        self.__data__.replace("\n","")
        video_tracks = self.__data__.split("'Tracks by Frame':[")

        blob_dict = eval(video_tracks[0]+'}')
        track_lines = (video_tracks[1]).split("]},")

        tracks_by_frame=[]
        
        for counter in track_lines[:-1]:
            temp_track = eval(counter+"]}")
            tracks_by_frame.append(temp_track)

        blob_dict['Tracks by Frame'] = tracks_by_frame
        
        for frame in blob_dict['Tracks by Frame']:
            for track in frame['Tracks']:
                x = 640/720.0*track['X']
                y = 480 - track['Y']
                track['X'] = x
                track['Y'] = y
                
        self.__data__ = blob_dict
        
    ########################################################################################################
    def __generateTrackIDs__(self):
        #Generate unique ID for each track segment, and ignoring short segments.
        track_id_max = 0
        active_track_numbers = []
        trac_dict = {}
        track_segments = {}
        good_tracks = {}
        num_frames = len(self.__data__['Tracks by Frame'])
        for frame_counter in range(0, num_frames):
            frame = self.__data__['Tracks by Frame'][frame_counter]
            frame_number = frame['Frame Number']

            if frame_counter:
                last_frame = self.__data__['Tracks by Frame'][frame_counter - 1]
            else:
                last_frame = frame

            for track_counter in range(0, len(frame['Tracks'])):

                track = frame['Tracks'][track_counter]
                current_track_num = track['Track Number']

                if current_track_num not in active_track_numbers:
                    active_track_numbers.append(current_track_num)
                    track_id_max += 1
                    trac_dict[current_track_num] = track_id_max
                    track['Track ID'] = trac_dict[current_track_num]
                    track_segments[track['Track ID']] = {'Distance':0.0, 'Total Frames':1, 'Start X':track['X'],'Start Y':track['Y'],
                                                         'End X':track['X'],'End Y':track['Y'], 'Sum Area':[track['Area']],
                                                         'Average Area':track['Area'], 'Start Frame':frame_number, 'Active Frames':1,
                                                         'Speed':0, 'Start Speed':0, 'End Speed':0, 'tempDist':[], 'Points':\
                                                         [[frame['Tracks'][track_counter]['X'], frame['Tracks'][track_counter]['Y']]]}
                else:    
                    track['Track ID'] = trac_dict[current_track_num]
                    if track['Frames Inactive'] > 0:
                        track_segments[track['Track ID']]['Total Frames'] += 1
                    else:
                        track_segments[track['Track ID']]['Total Frames'] += 1
                        track_segments[track['Track ID']]['Active Frames'] += 1
                        track_segments[track['Track ID']]['Sum Area'].append( track['Area'] )
                        track_segments[track['Track ID']]['Points'].append([frame['Tracks'][track_counter]['X'],\
                                                                            frame['Tracks'][track_counter]['Y']])
                    
                    for last_track_counter in range(0,len(last_frame['Tracks'])):
                        if last_frame['Tracks'][last_track_counter]['Track ID'] == track['Track ID']:
                            last_track = last_frame['Tracks'][last_track_counter]
                        else:
                            last_track = track
                    track_segments[track['Track ID']]['tempDist'].append( float(math.sqrt( (float(track['X'] - last_track['X']))**2 + \
                                         (float(track['Y'] - last_track['Y']))**2 )))
                    if track_segments[track['Track ID']]['Active Frames'] == 10:
                        track_segments[track['Track ID']]['Start Speed'] = sum(track_segments[track['Track ID']]['tempDist']) / 10.0


                            
                if frame_counter == num_frames-1:
                    active_track_numbers.remove(current_track_num)
                    trac_dict.pop(current_track_num)
                    track_segments[track['Track ID']]['Distance'] = sum(track_segments[track['Track ID']]['tempDist'])
                    track_segments[track['Track ID']]['Average Area'] = sum(track_segments[track['Track ID']]['Sum Area']) / \
                                                                        float(track_segments[track['Track ID']]['Active Frames'])
                    track_segments[track['Track ID']]['Speed'] = track_segments[track['Track ID']]['Distance'] / \
                                                                 track_segments[track['Track ID']]['Active Frames']
                    track_segments[track['Track ID']]['Max Area'] = max(track_segments[track['Track ID']]['Sum Area'])
                    track_segments[track['Track ID']].pop('Sum Area')
                    
                    if track_segments[track['Track ID']]['Active Frames'] >= 10:
                        track_segments[track['Track ID']]['End Speed'] = sum(track_segments[track['Track ID']]['tempDist'][-10:]) / 10.0
                    else:
                        track_segments[track['Track ID']]['End Speed'] = track_segments[track['Track ID']]['Speed']
                        track_segments[track['Track ID']]['Start Speed'] = track_segments[track['Track ID']]['Speed']

                    track_segments[track['Track ID']].pop('tempDist')
                    
                elif track['Frames Inactive'] >= self.__MAX_INACTIVE_FRAMES__:
                    if not current_track_num in [t['Track Number'] for t in self.__data__['Tracks by Frame'][frame_counter+1]['Tracks']] \
                        or self.__data__['Tracks by Frame'][frame_counter+1]['Frame Number'] > \
                           self.__data__['Tracks by Frame'][frame_counter]['Frame Number'] + self.__MAX_INACTIVE_FRAMES__:
                            
                        active_track_numbers.remove(current_track_num)
                        trac_dict.pop(current_track_num)
                        track_segments[track['Track ID']]['Distance'] = sum(track_segments[track['Track ID']]['tempDist'])
                        track_segments[track['Track ID']]['Average Area'] = sum(track_segments[track['Track ID']]['Sum Area']) / \
                                                                            float(track_segments[track['Track ID']]['Active Frames'])
                        track_segments[track['Track ID']]['End X'] = track['X']
                        track_segments[track['Track ID']]['End Y'] = track['Y']
                        track_segments[track['Track ID']]['Speed'] = track_segments[track['Track ID']]['Distance'] / \
                                                                     track_segments[track['Track ID']]['Active Frames']
                        track_segments[track['Track ID']]['Max Area'] = max(track_segments[track['Track ID']]['Sum Area'])
                        track_segments[track['Track ID']].pop('Sum Area')
                        

                        if track_segments[track['Track ID']]['Active Frames'] >= 10:
                            track_segments[track['Track ID']]['End Speed'] = sum(track_segments[track['Track ID']]['tempDist'][-10:]) / 10.0
                        else:
                            track_segments[track['Track ID']]['End Speed'] = track_segments[track['Track ID']]['Speed']
                            track_segments[track['Track ID']]['Start Speed'] = track_segments[track['Track ID']]['Speed']
                            
                        track_segments[track['Track ID']].pop('tempDist')

		#Filter Code
        count = 1
        for i in track_segments:
        #Basic Good track criteria            
            if (track_segments[i]['Active Frames']>=15 and 
                track_segments[i]['Distance'] > 7): # Adding to good tracks if pixel-distance of ay point in the track is greater than six from track start coordinates.                
                current =  1
                notGood = true
                segment = track_segments[i]
                try:                
                    while notGood:
                        if current > 9000:

                            #Assumption: A valid mouse object will meet criteria within five minutes or 9000 frames.
                            notGood = false #Then terminate loop.
                            #Centroid Pixel-distance travel criteria. Blob must at some point move more than 4 time the square root of its area from 
                            #Starting Position
                        if ((pow(segment['Points'][0][0] - segment['Points'][current][0], 2) + 
                             pow(segment['Points'][0][1] - segment['Points'][current][1], 2)) > 144):                
                                 good_tracks[count] = track_segments[i]
                                 count = count + 1
                                 notGood = false
                        current = current + 1
                except IndexError: #Iterate over list of points until exhaustion
                    pass
                
        self.__data__['Segment Info'] = good_tracks     
    ########################################################################################################
    def load(self, *args, **kwargs):
        '''Load the track data from file'''
        self.__data__ = {}
        if kwargs.get('filename'):
            self.__filename__ = kwargs.get('filename')
            if '.p2' in self.__filename__:
                if kwargs.get('rebuild') == true:
                    self.__data__ = loadFile(self.__filename__, "rb")
                    self.__generateTrackIDs__()
                    #self.joinTracks()
                    self.__data__['Version'] = CURRENT_VERSION
                    if kwargs.get('save') == true:
                        self.save()
                    print "Updated data to ", CURRENT_VERSION, "."
                    
                else:
                    self.__data__ = loadFile(self.__filename__, "rb")
                    self.__DATA_VERSION__ = self.__data__.get('Version')
                    if self.__DATA_VERSION__ < CURRENT_VERSION:
                        self.__generateTrackIDs__()
                        #self.joinTracks()
                        self.__data__['Version'] = CURRENT_VERSION
                        if kwargs.get('save') == true:
                            self.save()
                        print "Updated data to ", CURRENT_VERSION, "."

            else:
                self.__data__ = loadFile(self.__filename__, "r")
                self.__parseRawData__()
                self.__generateTrackIDs__()
                #self.joinTracks()
                self.__data__['Version'] = CURRENT_VERSION
                if kwargs.get('save') == true:
                    self.save()
                
        elif self.__filename__:
            if '.p2' in self.__filename__:
                self.__data__ = loadFile(self.__filename__, "rb")
                self.__DATA_VERSION__ = self.__data__.get('Version')
                if self.__DATA_VERSION__ < CURRENT_VERSION:
                    self.__generateTrackIDs__()
                    #self.joinTracks()
                    self.__data__['Version'] = CURRENT_VERSION
                    #self.save()
                    print "Updated data to ", CURRENT_VERSION, "."

            else:
                self.__data__ = loadFile(self.__filename__, "r")
                self.__parseRawData__()
                self.__generateTrackIDs__()
                #self.joinTracks()
                self.__data__['Version'] = CURRENT_VERSION
                #self.save()
            
    ########################################################################################################
    def save(self):
        '''Save the track data to file'''
        if self.__filename__:
            if '.p2' in self.__filename__:
                output = open(self.__filename__, "wb")
                cPickle.dump(self.__data__, output, 2)
                output.close()
            else:
                output = open(self.__filename__.replace(".raw", ".p2"), "wb")
                cPickle.dump(self.__data__, output, 2)
                output.close()
        else:
            print "No filename attached to tracker. Please load data from a file using load( filename = \"myfile\")."

    ########################################################################################################
    def getObjectTimes(self, min_size = 50, max_size = 175, min_length = 30):
        '''Print the entry time of all objects in range (min_size, max_size) with lifetime greater than min_length frames.'''
        for counter in self.__data__['Segment Info']:
            track = self.__data__['Segment Info'][counter]

            if track['Total Frames'] > min_length:
                if track['Average Area'] > min_size and track['Average Area'] < max_size:
                    start = time.strftime('%H:%M:%S', time.gmtime(track['Start Frame']/self.__FPS__))
                    end = time.strftime('%H:%M:%S', time.gmtime((track['Start Frame'] + track['Total Frames']) / self.__FPS__))

                    if track['Start X'] < 360 and track ['Start Y'] < 240:
                        quadrant = 'First'
                    elif track['Start X'] < 360 and track ['Start Y'] > 240:
                        quadrant = 'Third'
                    elif track['Start X'] > 360 and track ['Start Y'] < 240:
                        quadrant = 'Second'
                    else:
                        quadrant = 'Fourth'
            
                    print "Size = " + str(track['Average Area']) + ', Start time = ' + start \
                          + ', End time = ' + end + ', Quadrant = ' + quadrant
    ########################################################################################################
    def setJoinConstants(self, TIMEC, SPACEC, SPEEDC, SIZEC ):
        '''Set constants used for track joining.'''
        self.__TIMEC__ = TIMEC
        self.__SPACEC__ = SPACEC
        self.__SPEEDC__ = SPEEDC
        self.__SIZEC__ = SIZEC

    ########################################################################################################
    def drawHistogram(self, min_size = 30, log_power = 1.2, bar_width = 25, height_scale = 3):
        '''Generate size distribution diagram, colored by number of frames object was active. X axis is the
            average size of the object, Y axis is arbitrary. Red = 10 seconds, purple = 5 seconds,
            bluepurple = 3 seconds, green = 2 seconds, light green = 1 second, yellow = .5 seconds. Anything with
            an average area of less than 25 pixels is considered garbage and thus ignored.'''
        bin_sizes = [min_size]
        size_data = {'Occurance':[0 for x in range(16)], 'Average Framecount':[0 for x in range(16)]}
        
        for counter in range(20):
            bin_sizes.append(bin_sizes[counter]*log_power)
        print "Collecting size data....                                    ",
        for track_counter in self.__data__['Joined Tracks']:
            track = self.__data__['Segment Info'][track_counter]

            if 0 < track['Average Area'] < bin_sizes[0]:
                size_data['Occurance'][0] += 1
                size_data['Average Framecount'][0] += track['Total Frames']
            elif bin_sizes[0] < track['Average Area'] < bin_sizes[1]:
                size_data['Occurance'][1] += 1
                size_data['Average Framecount'][1] += track['Total Frames']
            elif bin_sizes[1] < track['Average Area'] < bin_sizes[2]:
                size_data['Occurance'][2] += 1
                size_data['Average Framecount'][2] += track['Total Frames']
            elif bin_sizes[2] < track['Average Area'] < bin_sizes[3]:
                size_data['Occurance'][3] += 1
                size_data['Average Framecount'][3] += track['Total Frames']
            elif bin_sizes[3] < track['Average Area'] < bin_sizes[4]:
                size_data['Occurance'][4] += 1
                size_data['Average Framecount'][4] += track['Total Frames']
            elif bin_sizes[4] < track['Average Area'] < bin_sizes[5]:
                size_data['Occurance'][5] += 1
                size_data['Average Framecount'][5] += track['Total Frames']
            elif bin_sizes[5] < track['Average Area'] < bin_sizes[6]:
                size_data['Occurance'][6] += 1
                size_data['Average Framecount'][6] += track['Total Frames']
            elif bin_sizes[6] < track['Average Area'] < bin_sizes[7]:
                size_data['Occurance'][7] += 1
                size_data['Average Framecount'][7] += track['Total Frames']
            elif bin_sizes[7] < track['Average Area'] < bin_sizes[8]:
                size_data['Occurance'][8] += 1
                size_data['Average Framecount'][8] += track['Total Frames']
            elif bin_sizes[8] < track['Average Area'] < bin_sizes[9]:
                size_data['Occurance'][9] += 1
                size_data['Average Framecount'][9] += track['Total Frames']
            elif bin_sizes[9] < track['Average Area'] < bin_sizes[10]:
                size_data['Occurance'][10] += 1
                size_data['Average Framecount'][10] += track['Total Frames']
            elif bin_sizes[10] < track['Average Area'] < bin_sizes[11]:
                size_data['Occurance'][11] += 1
                size_data['Average Framecount'][11] += track['Total Frames']
            elif bin_sizes[11] < track['Average Area'] < bin_sizes[12]:
                size_data['Occurance'][12] += 1
                size_data['Average Framecount'][12] += track['Total Frames']
            elif bin_sizes[12] < track['Average Area'] < bin_sizes[13]:
                size_data['Occurance'][13] += 1
                size_data['Average Framecount'][13] += track['Total Frames']
            elif bin_sizes[13] < track['Average Area'] < bin_sizes[14]:
                size_data['Occurance'][14] += 1
                size_data['Average Framecount'][14] += track['Total Frames']
            else:
                size_data['Occurance'][15] += 1
                size_data['Average Framecount'][15] += track['Total Frames']
        print "Done."

        for counter in range(len(size_data['Average Framecount'])):
            if size_data['Occurance'][counter]:
                size_data['Average Framecount'][counter] /= size_data['Occurance'][counter]
        #print size_data['Occurance']
    
        plot = Graphics()
                    
        for counter in range(len(size_data['Average Framecount'])-1):
            occurance = size_data['Occurance'][counter]
            framecount = int(size_data['Average Framecount'][counter])
            label = 'Occurance: %(occurance)3d' % vars() + '. Average Framecount: %(framecount)3d' % vars() + '.'
            plot += polygon( [[counter*bar_width,   0], \
                                [counter*bar_width,   height_scale*min(250, size_data['Occurance'][counter])], \
                                [(counter+1)*bar_width, height_scale*min(250, size_data['Occurance'][counter])],\
                                [(counter+1)*bar_width, 0]], fill=true,\
                                 rgbcolor = hue(size_data['Average Framecount'][counter]*.005), legend_label = label)

        
        #plot += bar_chart(size_data['Occurance'], width=1)
        print "Generating output....",

        gap = 5

        ymax = min(250, max([max(size_data['Occurance'])+(max(size_data['Occurance'])/25),150]))
        
        plot += line([(0,0),(0,ymax*height_scale)], color = 'black', thickness = .5)
        plot += line([(0,0),(bar_width*len(bin_sizes),0)], color = 'black', thickness = .5)

        for counter in range(0, len(bin_sizes)):
            plot += line([(counter*bar_width+bar_width, 0), (counter*bar_width+bar_width,5)], color = 'black', thickness = .5)
            plot += text(str(round(bin_sizes[counter])), (counter*bar_width + bar_width, -5), color = 'black' )
        
        for counter in range(1, ymax):
            if not counter % gap:
                plot += line([(0, height_scale*counter), (5,height_scale*counter)], color = 'black', thickness = .5)
                plot += text(str(counter), (-20,counter*height_scale), color = 'black' )

        rcParams['font.monospace'] = ['DejaVu Sans Mono']
        plot.set_legend_options(font_family = 'monospace', shadow = true, fancybox = true)
        plot.save( self.__filename__.rsplit('.',2)[0] + "sizes.pdf", xmin = 0, ymin = 0, figsize = [30,10], axes = false)
        #plot.show()
        print "Done."
        
    ########################################################################################################
    def getObjectCategory(self, track):
        #print self.__data__['Segment Info']

        #SMALL_SIZE_UB = [125, 150, 110, 110, 105, 150, 150, 100, 100]

        avg = track['Average Area']
        spd = track['Speed']
        if  self.__SMALL_SIZE_LB__ < avg and avg < self.__SMALL_SIZE_UB__:
            if spd > self.__SLOW_SPEED_UB__:
                return 'Fast'
            else:
                return 'Small'
        elif avg < self.__MID_SIZE_UB__:
            if spd > self.__SLOW_SPEED_UB__:
                return 'Fast'
            else:
                return 'Medium'
        else:
            return 'Large'

    ########################################################################################################
    def getRegionActivity(self, framesIn, framesOut, entrances, exits):
#==============================================================================
#     '''Imports a prepared mask image file,generates a framecount of tracks
#             with respect to frames spent inside and outside nest boundary. 
#             Parameters are predefined variables in calling module.   
#             mask[x,y][0] = > 200 means track is in nest region.
#             mask[x,y][0] = < 100 means track outside any defined nest are 
#         
#==============================================================================
        import cv2
        #Load Image
        mask = cv2.imread("mask.png")
        framesIn = 0
        framesOut = 0
        entrances = 0
        exits = 0
        for segment in self.__data__['Segment Info'].values():
			if self.getObjectCategory(segment) == 'Small': #Object only processed as mouse if it registers as small
				segment['framesIn'] = 0
				segment['framesOut'] = 0
				segment['entrances'] = 0
				segment['exits'] = 0
				for p_counter in range(len(segment['Points'])):
					#print segment['Points'][p_counter]
					current = ([int(segment['Points'][p_counter][0]),
								int(segment['Points'][p_counter][1])])
								#current[0] = y coordinate, current[1] = x coordinate 
								#checks to see if we are at the first frame of the segment.             
					if p_counter: 
						previous = ([int(segment['Points'][p_counter-1][0]),
									int(segment['Points'][p_counter-1][1])])
					else:
						previous = current
					#Signal present region of current segment point.
					#Incrementing counters.              
					if mask[current[1], current[0]][0] > 200:
						framesIn = framesIn + 1
						segment['framesIn'] = segment['framesIn'] + 1
					else: 
						framesOut = framesOut +1
						segment['framesOut'] = segment['framesOut'] + 1
					#Signal entrance and exit events by comparison of present and previous.
					#Incrementing counters.
					if (mask[current[1], current[0]][0] > 200 and
						mask[previous[1], previous[0]][0] < 100): #Entrance
						entrances = entrances + 1
						segment['entrances'] = segment['entrances'] + 1
					if (mask[current[1], current[0]][0] < 100 and
						mask[previous[1], previous[0]][0] > 200): #Exit)
						exits = exits + 1
						segment['exits'] = segment['exits'] + 1
        return (framesIn, framesOut, entrances, exits) 
         
            
 ########################################################################################################
    def drawActivityDiagram(self, joined = false, start_frame = 0, frames_per_point = 29.97*30 ):
        counter = 0
        point_list = {'Small':[], 'Medium':[], 'Large':[], 'Fast':[] }
        current_id_list = {'Small':set(), 'Medium':set(), 'Large':set(), 'Fast':set() }
        current_frame_UB = frames_per_point

        for frame in self.__data__['Tracks by Frame']:
            if frame['Frame Number'] > current_frame_UB:
                for key in point_list:
                    point_list[key].append([ current_frame_UB / frames_per_point , len(current_id_list[key])])
                current_id_list = {'Small':set(), 'Medium':set(), 'Large':set(), 'Fast':set() }
                current_frame_UB += frames_per_point
            for track in frame['Tracks']:
                if track['Track ID'] in self.__data__['Segment Info']:
                    segment = self.__data__['Segment Info'][track['Track ID']]
                    if segment.get('Joined ID'):
                        cat = self.getObjectCategory(self.__data__['Joined Tracks'][segment['Joined ID']])
                        current_id_list[cat].add(segment['Joined ID'])
                        
                    
        plot = Graphics()
        for key in point_list:
            counter += .25
            plot += list_plot(point_list[key], plotjoined = joined, color = hue(counter), \
                              legend_label = key)

        #plot.show()
        plot.set_legend_options(font_family = 'monospace', shadow = true, fancybox = true)
        plot.save( self.__filename__.rsplit('.',2)[0] + "activity" + str(int(frames_per_point/29.97)) +\
                   ".pdf", xmin = 0, ymin = 0, figsize = [30,10])
        
    ########################################################################################################
    def drawTracksNew(self, tMin, tMax, minActive):
		plot = Graphics()
		#longest = []
		#for index1 in self.__data__['Segment Info']:
		#	seg = self.__data__['Segment Info'][index1]
		#	longest.append(seg['Active Frames'])

		#longestTen = []
		#for count in range(10):
		#	longestTen.append(max(longest))
		#	longest.remove(max(longest))
		#print longestTen
		totalFrames = 0;
		for index in self.__data__['Segment Info']:
			seg = self.__data__['Segment Info'][index]
			
			start = time.strftime('%H:%M:%S', time.gmtime(seg['Start Frame'] / self.__FPS__))
			end = time.strftime('%H:%M:%S', time.gmtime((seg['Active Frames'] + seg['Start Frame']) / self.__FPS__))

			totalFrames += seg['Active Frames']
			if tMin <= seg['Start Frame'] <= tMax:
					if seg['Active Frames'] > minActive:	
						#plot += point( seg['Points'][0], color = 'black', size = 2)
						plot += text(str(index), seg['Points'][0], color = 'black')
						plot += list_plot(seg['Points'], \
								color = hue(uniform(0,1)), thickness = 1, \
						legend_label = 'Index: ' + str(index) + ', Time: ' + start + ' to ' + end)
					else:
						plot += list_plot(seg['Points'], \
								color = hue(uniform(0,1)), thickness = 1)
					
				
		plot.save( self.__filename__.rsplit('.',2)[0] + 'segments' + ".pdf", xmin = 0, ymin = 0,\
				   xmax = 640, ymax = 480 , figsize = [10,8])
		print "Total frames: " + str(totalFrames)

    def drawTracks(self, joined = True, color_method = 'importance', min_time = 15):
        '''Generate a graphic representation of all tracks'''
        def colorByTime(time):
            if time < 30*60*15:
                return 'cyan'
            elif time < 30*60*30:
                return 'blue'
            elif time < 30*60*45:
                return 'darkblue'
            elif time < 30*60*60:
                return 'darkgreen'
            elif time < 30*60*75:
                return 'green'
            elif time < 30*60*90:
                return 'lightgreen'
            elif time < 30*60*105:
                return 'yellow'
            elif time < 30*60*120:
                return 'orange'
            elif time < 30*60*135:
                return 'red'

        self.__FPS__ = 29.97
        points = {}
        trackIDs = []
        color_method = color_method.upper()
        longest_tracks = [0]
        if color_method == "IMPORTANCE":
            color_index = .05
        myplot = Graphics()

        if color_method == "TIME" :
            for counter in points:
                current = points[counter]
                if len(current['Points']) > 80:
                    if joined:
                        myplot += list_plot(current['Points'], plotjoined = True, \
                                            color = colorByTime(current['Start Time']), thickness = max([1,sqrt(current['Size']) / 2.0]))
                    else:
                        myplot += list_plot(points[counter]['Points'], plotjoined = False, \
                                            color = colorByTime(current['Start Time']), size = max([1,sqrt(current['Size']) / 2.0]))
                        
                elif len(current['Points']) > min_time:
                    myplot += list_plot(current['Points'], color = colorByTime(current['Start Time']), \
                                        size = max([1, sqrt(current['Size']) / 2]))
                    
        elif color_method == "ID":
            for counter in points:
                current = points[counter]
                if len(current['Points']) > 80:
                    if joined:
                        myplot += list_plot(current['Points'], plotjoined = True, \
                                            color = hue(counter*.005), thickness = max([1, sqrt(current['Size']) / 2.0]))
                    else:
                        myplot += list_plot(points[counter]['Points'], plotjoined = False, \
                                            color = hue(counter*.005), size = max([1, sqrt(current['Size']) / 2.0]))
                        
                elif len(current['Points']) > min_time:
                    myplot += list_plot(points[counter]['Points'], color = hue(counter*.005), \
                                        size = max([1, sqrt(points[counter]['Size']) / 2]))
                        
        elif color_method == "SEGMENTS":
            plot = Graphics()
            longest = []
            for index1 in self.__data__['Segment Info']:
                seg = self.__data__['Segment Info'][index1]
                longest.append(seg['Active Frames'])

            longestTen = []
            for count in range(min(10,len(self.__data__['Segment Info']))):
                longestTen.append(max(longest))
                longest.remove(max(longest))
            print longestTen
            for index in self.__data__['Segment Info']:
                seg = self.__data__['Segment Info'][index]

                start = time.strftime('%H:%M:%S', time.gmtime(seg['Start Frame'] / self.__FPS__))
                end = time.strftime('%H:%M:%S', time.gmtime((seg['Active Frames'] + seg['Start Frame']) / self.__FPS__))

                
                if seg['Active Frames'] in longestTen:
                    plot += list_plot(seg['Points'], plotjoined = joined, \
                        color = hue(uniform(0,1)), thickness = 1, \
                        legend_label = 'Index: ' + str(index) + ', Time: ' + start + ' to ' + end)
                    plot += point( seg['Points'][0], color = 'black', size = 2)
                    plot += text(str(index), seg['Points'][0], color = 'black')
                elif len(seg['Points']) >= 60:
                    plot += list_plot(seg['Points'], plotjoined = joined, color = hue(uniform(0,1)), thickness = 1)
                    plot += point( seg['Points'][0], color = 'black', size = 2)
                        
                else:
                    plot += list_plot(seg['Points'], plotjoined = false, color = hue(uniform(0,1)), size = 1)
                    #plot += text(str(index), seg['Points'][0], color = 'black')

            plot.save("." + self.__filename__[1:].rsplit('.',2)[0] + 'segments' + ".pdf", xmin = 0, ymin = 0,\
				   xmax = 640, ymax = 480 , figsize = [10,8])
                       
            print len(plot)
            
        elif color_method == "IMPORTANCE":
            maxsize = 0
            maxspeed = 0
            for counter in self.__data__['Segment Info']:
                minimum = min(longest_tracks)
                if points[counter]['Size'] > maxsize and len(points[counter]['Points']) > 60:
                        maxsize = points[counter]['Size']
                if points[counter]['Avg Speed'] > maxspeed and len(points[counter]['Points']) > 20:
                    maxspeed = points[counter]['Avg Speed']
                if len(points[counter]['Points']) > minimum:
                    longest_tracks.append(len(points[counter]['Points']))
                    if len(longest_tracks) > 13:
                        longest_tracks.remove(minimum)       


            for counter in points:
                if points[counter]['Size'] == maxsize:
                    start = time.strftime('%H:%M:%S', time.gmtime(points[counter]['Start Time'] / self.__FPS__))
                    end = time.strftime('%H:%M:%S', time.gmtime(points[counter]['End Time'] / self.__FPS__))
                    if joined and len(points[counter]['Points']) > 150:
                        myplot += list_plot(points[counter]['Points'], plotjoined = True, \
                                            color = hue(1), thickness = max([1,sqrt(points[counter]['Size']) / 2.0]), \
                                            legend_label = 'Time: ' + start + ' to ' + end)
                    else:
                        myplot += list_plot(points[counter]['Points'], plotjoined = False, \
                                            color = hue(1), size = max([1,sqrt(points[counter]['Size']) / 2.0]), \
                                            legend_label = 'Time: ' + start + ' to ' + end)
                        
                elif points[counter]['Avg Speed'] == maxspeed:
                    start = time.strftime('%H:%M:%S', time.gmtime(points[counter]['Start Time'] / self.__FPS__))
                    end = time.strftime('%H:%M:%S', time.gmtime(points[counter]['End Time'] / self.__FPS__))
                    if joined and len(points[counter]['Points']) > 150:
                        myplot += list_plot(points[counter]['Points'], plotjoined = True, \
                                            color = 'black', thickness = max([1,sqrt(points[counter]['Size']) / 2.0]), \
                                            legend_label = 'Time: ' + start + ' to ' + end)
                    else:
                        myplot += list_plot(points[counter]['Points'], plotjoined = False, \
                                            color = 'black', size = max([1,sqrt(points[counter]['Size']) / 2.0]), \
                                            legend_label = 'Time: ' + start + ' to ' + end)
                        
                elif len(points[counter]['Points']) > min(longest_tracks):
                    color_index += .05
                    start = time.strftime('%H:%M:%S', time.gmtime(points[counter]['Start Time'] / self.__FPS__))
                    end = time.strftime('%H:%M:%S', time.gmtime(points[counter]['End Time'] / self.__FPS__))
                    if joined:
                        myplot += list_plot(points[counter]['Points'], plotjoined = True, \
                                            color = hue(color_index), thickness = max([1,sqrt(points[counter]['Size']) / 2.0]), \
                                            legend_label = 'Time: ' + start + ' to ' + end)
                    else:
                        myplot += list_plot(points[counter]['Points'], plotjoined = False, \
                                            color = hue(color_index), size = max([1,sqrt(points[counter]['Size']) / 2.0]), \
                                            legend_label = 'Time: ' + start + ' to ' + end)
                        
                elif len(points[counter]['Points']) > 150:
                    if joined:
                        myplot += list_plot(points[counter]['Points'], plotjoined = True, \
                                            color = hue(uniform(.7,.9)), thickness = max([1, sqrt(points[counter]['Size']) / 2.0]))
                    else:
                        myplot += list_plot(points[counter]['Points'], plotjoined = False, \
                                            color = hue(uniform(.7,.9)), size = max([1, sqrt(points[counter]['Size']) / 2.0]))


                elif len(points[counter]['Points']) > min_time:
                    myplot += list_plot(points[counter]['Points'], color = 'darkgrey', \
                                        size = max([1, sqrt(points[counter]['Size']) / 2]))
                    
        elif color_method == "JOINED":
            plot = Graphics()
            
            for key in self.__data__['Joined Tracks']:
                trackList = self.__data__['Joined Tracks'][key]
                color = hue(uniform(0,1))
                length = len(trackList['Tracks'])
                if length:
                    for counter in range(length):
                        ID = trackList['Tracks'][counter]
                        if counter > 0:
                            plot += line( [self.__data__['Segment Info'][trackList['Tracks'][counter-1]]['Points'][-1], \
                                               self.__data__['Segment Info'][ID]['Points'][0]], color = color, thickness = .5, \
                                               linestyle = ':', alpha = .5 )
                            if self.__data__['Segment Info'][trackList['Tracks'][counter]]['Active Frames'] > 30 and joined:
                                plot += list_plot(self.__data__['Segment Info'][ID]['Points'], plotjoined = joined,
                                                      color = color, thickness = 1, alpha = .5)
                            else:
                                plot += list_plot(self.__data__['Segment Info'][ID]['Points'], plotjoined = false,
                                                      color = color, size = 1, alpha = .5)                                
                            plot += point(self.__data__['Segment Info'][ID]['Points'][0], color = 'black', size = 1, alpha = .75)
                            #plot += text(str(trackList['Tracks'][counter]), self.__data__['Segment Info'][ID]['Points'][0], fontsize = 6, color = 'black')
                        else:
                            start = time.strftime('%H:%M:%S', time.gmtime(trackList['Start Frame'] / self.__FPS__))
                            end = time.strftime('%H:%M:%S', time.gmtime(trackList['End Frame'] / self.__FPS__))
                            if trackList['Total Frames'] > 90 or trackList['Speed'] > 1.5:
                                label = 'ID: ' + "%4d" % key + ' Time: ' + start + ' to ' + end + '. Category: '\
                                        + "%6s" % trackList['Category'] + ' - ' + "%8.2f" % trackList['Average Area'] + '. Speed: ' +\
                                        "%.3f" % trackList['Speed'] + '.'
                                label = 'ID: ' + "%4d" % key + ' Time: ' + start + ' to ' + end + '. Category: '\
                                        + "%6s" % trackList['Category'] + '.'
                                
                                if self.__data__['Segment Info'][ID]['Active Frames'] > 30:
                                    if joined:
                                        plot += list_plot(self.__data__['Segment Info'][ID]['Points'], plotjoined = true,
                                                              color = color, thickness = 1, alpha = .5, legend_label = label)
                                    else:
                                        plot += list_plot(self.__data__['Segment Info'][ID]['Points'], plotjoined = false,
                                                              color = color, size = 1, alpha = .5, legend_label = label)
                                    plot += point(self.__data__['Segment Info'][ID]['Points'][0], color = 'black', size = 1, alpha = .75)
                                    plot += text(str(key), self.__data__['Segment Info'][ID]['Points'][0], color = color)
                                    
                                else:
                                    plot += list_plot(self.__data__['Segment Info'][ID]['Points'], plotjoined = false,
                                                          color = color, size = 1, alpha = .5, legend_label = label)
                                    plot += point(self.__data__['Segment Info'][ID]['Points'][0], color = 'black', size = 1, alpha = .75)
                                    plot += text(str(key), self.__data__['Segment Info'][ID]['Points'][0], color = color)

                            else:
                                if self.__data__['Segment Info'][ID]['Active Frames'] > 30:
                                    if joined:
                                        plot += list_plot(self.__data__['Segment Info'][ID]['Points'], plotjoined = true,
                                                          color = color, thickness = 1, alpha = .5)
                                    else:
                                        plot += list_plot(self.__data__['Segment Info'][ID]['Points'], plotjoined = false,
                                                          color = color, size = 1, alpha = .5)
                                    plot += point(self.__data__['Segment Info'][ID]['Points'][0], color = 'black', size = 1, alpha = .75)
                                    plot += text(str(key), self.__data__['Segment Info'][ID]['Points'][0], color = color)
                                    
                                elif length > 1:
                                    plot += list_plot(self.__data__['Segment Info'][ID]['Points'], plotjoined = false,
                                                          color = color, size = 1, alpha = .5)
                                    plot += point(self.__data__['Segment Info'][ID]['Points'][0], color = 'black', size = 1, alpha = .75)
                                    plot += text(str(key), self.__data__['Segment Info'][ID]['Points'][0], color = color)
                                else:
                                    plot += list_plot(self.__data__['Segment Info'][ID]['Points'], plotjoined = false,
                                                          color = 'darkgrey', size = 1, alpha = .5)
                                    plot += point(self.__data__['Segment Info'][ID]['Points'][0], color = 'black', size = 1, alpha = .75)
                                    plot += text(str(key), self.__data__['Segment Info'][ID]['Points'][0], fontsize = 5, color = 'black')

                                

            plot.save( self.__filename__.rsplit('.',2)[0] + 'joined' + ".pdf", xmin = 0, ymin = 0,\
                       xmax = 720, ymax = 720 , figsize = [12,12])

            
        elif color_method == "ELABORATE":
            plotList = [ Graphics() for x in range(11) ]
            fullPlot = Graphics()
            minute = self.__FPS__ * 60
            
            for key in self.__data__['Joined Tracks']:
                trackList = self.__data__['Joined Tracks'][key]
                plotTemp = Graphics()
                color = hue(uniform(0,1))
                for counter in range(len(trackList['Tracks'])):
                    ID = trackList['Tracks'][counter]
                    if counter > 0:
                        plotTemp += line( [self.__data__['Segment Info'][trackList['Tracks'][counter-1]]['Points'][-1], \
                                           self.__data__['Segment Info'][ID]['Points'][0]], color = color, thickness = .5, \
                                           linestyle = ':', alpha = .5 )
                        plotTemp += list_plot(self.__data__['Segment Info'][ID]['Points'], plotjoined = joined,
                                              color = color, thickness = 1, alpha = .5)
                    else:
                        start = time.strftime('%H:%M:%S', time.gmtime(trackList['Start Frame'] / self.__FPS__))
                        end = time.strftime('%H:%M:%S', time.gmtime(trackList['End Frame'] / self.__FPS__))

                        if trackList['End Frame'] - trackList['Start Frame'] > 90:
                            label = 'ID: ' + "%4d" % key + ' Time: ' + start + ' to ' + end + '. Category: '\
                                    + "%6s" % trackList['Category'] + ' - ' + "%8.2f" % trackList['Average Area'] + '. Speed: ' +\
                                    "%.3f" % trackList['Speed'] + '.'
                            label = 'ID: ' + "%4d" % key + ' Time: ' + start + ' to ' + end + '. Category: '\
                                    + "%6s" % trackList['Category'] + '.'
                            
                            plotTemp += list_plot(self.__data__['Segment Info'][ID]['Points'], plotjoined = joined,
                                                  color = color, thickness = 1, alpha = .5, legend_label = label)
                            plotTemp += text(str(key), self.__data__['Segment Info'][ID]['Points'][0], color = color)
                        else:
                            plotTemp += list_plot(self.__data__['Segment Info'][ID]['Points'], plotjoined = false,
                                                  color = 'grey', size = 1, alpha = .5)
                            plotTemp += point(self.__data__['Segment Info'][ID]['Points'][0], color = 'black', size = 1)
                            
                if trackList['Start Frame'] < 15*minute:
                    plotList[0] += plotTemp
                elif trackList['Start Frame'] < 30*minute:
                    plotList[1] += plotTemp
                elif trackList['Start Frame'] < 45*minute:
                    plotList[2] += plotTemp
                elif trackList['Start Frame'] < 60*minute:
                    plotList[3] += plotTemp
                elif trackList['Start Frame'] < 75*minute:
                    plotList[4] += plotTemp
                elif trackList['Start Frame'] < 90*minute:
                    plotList[5] += plotTemp
                elif trackList['Start Frame'] < 105*minute:
                    plotList[6] += plotTemp
                elif trackList['Start Frame'] < 120*minute:
                    plotList[7] += plotTemp
                elif trackList['Start Frame'] < 135*minute:
                    plotList[8] += plotTemp
                else:
                    plotList[9] += plotTemp
                
            for plot in plotList:
                if plot:
                    plot.set_legend_options(font_family = 'monospace', shadow = true, fancybox = true)
                    plot.save( self.__filename__.rsplit('.',2)[0] + 'Ela' + str(plotList.index(plot)) + ".pdf",\
                               xmin = 0, ymin = 0, xmax = 1200, ymax = 1000 , figsize = [12,10])                            
        else:
            print "Invalid color method. Ending...."
            return
                    

        print "Done."
        print "Displaying output....                      ",
        if myplot:
            myplot.save( self.__filename__.rsplit('.',2)[0] + color_method.capitalize() + ".pdf", xmin = 0, ymin = 0, figsize=[16,12] )
        print "Done."
    ########################################################################################################
    def drawSpectrogram(self):

        plot = line([])

        print "Generating output....                      ",
        for counter in self.__data__['Joined Tracks']:
            current = self.__data__['Joined Tracks'][counter]
            plot += line( ([current['Average Area'], 0], [current['Average Area'], 1]), thickness = 1, color = 'grey', alpha = .1)          

        #print "Maximum object size was: " + str(max( x[0] for x in size_data )) + "."
                    
        plot.save( self.__filename__.rsplit('.',2)[0] + "spectro.pdf", xmin = 0, ymin = 0, xmax = 720, figsize=[30,10] )
        print "Done."

      #######################################################################################################   
    def drawSpeedSpectrogram(self, segments = false):

        plot = line([])

        print "Generating output....                      ",

        if segments:
            for counter in self.__data__['Segment Info']:
                current = self.__data__['Segment Info'][counter]
                plot += line( ([current['Speed'], 0], [current['Speed'], 1]), thickness = 1, color = 'blue', alpha = .15)          
                plot += text(str(counter),[current['Speed'], uniform(0,1)], color = 'black')
        else:
            for counter in self.__data__['Joined Tracks']:
                current = self.__data__['Joined Tracks'][counter]
                plot += line( ([current['Speed'], 0], [current['Speed'], 1]), thickness = 1, color = 'blue', alpha = .15)          
                plot += text(str(counter),[current['Speed'], uniform(0,1)], color = 'black')
        #print "Maximum object size was: " + str(max( x[0] for x in size_data )) + "."
                    
        plot.save( self.__filename__.rsplit('.',2)[0] + "speedSpectro.pdf", xmin = 0, ymin = 0, xmax = 20, figsize=[20,10] )
        print "Done."


    ########################################################################################################
    def joinTracks(self):
        '''Create a list of tracks which should belong to the same object'''

        print "Joining tracks....              "
        
        def cmpDist(a,b):
            return cmp(a[2],b[2])
        def cmpFirstElement(a,b):
            return cmp(a[0],b[0])
        
        cart = CartesianProduct(self.__data__['Segment Info'], self.__data__['Segment Info'])
        joinedPairs = []

        for iterable in cart:
            first = self.__data__['Segment Info'][iterable[0]]
            second = self.__data__['Segment Info'][iterable[1]]
            if(self.__data__['Segment Info'][iterable[0]]['Start Frame'] < self.__data__['Segment Info'][iterable[1]]['Start Frame']):
                first = self.__data__['Segment Info'][iterable[0]]
                second = self.__data__['Segment Info'][iterable[1]]
            elif (self.__data__['Segment Info'][iterable[0]]['Start Frame'] < self.__data__['Segment Info'][iterable[1]]['Start Frame']):
                first = self.__data__['Segment Info'][iterable[1]]
                second = self.__data__['Segment Info'][iterable[0]]
            if iterable[0] != iterable[1]:    
                timeDist = second['Start Frame'] - (first['Active Frames'] + first['Start Frame'])

                    
                spaceDist = sqrt( (first['End X'] - second['Start X'])**2 + (first['End Y'] - second['Start Y'])**2)
                sizeDist = abs( 1 - ( first['Average Area'] / second['Average Area'] ) )
                speedDist = first['End Speed'] - second['Start Speed']

                if first['End Speed'] == 0:
                    if spaceDist < 5:
                        std = 0
                    else:
                        std = 1
                else:
                    std = spaceDist / max(first['End Speed'],second['Start Speed'])

                if timeDist == 0:
                    dist = spaceDist
                else:
                    dist = abs( std / timeDist )

                dist += ( abs(iterable[0] - iterable[1]) / 5.0 )

                if len(first['Points']) > 1:
                    v1x = first['Points'][-1][0] - first['Points'][-2][0]
                    v1y = first['Points'][-1][1] - first['Points'][-2][1]
                else:
                    v1x = 0
                    v1y = 0
                if len(second['Points']) > 1:
                    v2x = second['Points'][1][0] - second['Points'][0][0]
                    v2y = second['Points'][1][1] - second['Points'][0][1]
                else:
                    v2x = 0
                    v2y = 0

                    
                n1 = sqrt( v1x**2 + v1y**2 )
                n2 = sqrt( v2x**2 + v2y**2 )

                if (v1x == 0 and v1y == 0):
                    angle = 0
                elif (v2x == 0 and v2y == 0):
                    angle = 0
                else:
                    angle = float(arccos( (v1x*v2x + v1y*v2y)  / (n1 * n2) ) / pi)

                
                if iterable[0] in [338,339] and iterable[1] in [338,339]:
                   print iterable[0], iterable[1], " std: ", std, " dst: ", dist, " angle: ", angle, " td: ", timeDist, " spcd: ", spaceDist, " sizd: ", sizeDist
                
                if first['Speed'] > 2.0:
                    if (-4 <= timeDist <= 10) and spaceDist < 75 and (0 <= sizeDist < 4) and dist < 20:
                        #dist = timeDist / abs( 1 - (spaceDist / (max(first['End Speed'],.1)))) + speedDist
                        joinedPairs.append([ iterable[0], iterable[1], dist+angle])
                        #print spaceDist, ' ', timeDist, ' ', sizeDist, ' ', speedDist
                else:
                    if (-4 <= timeDist <= 330) and spaceDist < 20 and (0 <= sizeDist < 3) and dist < 10:
                        #dist = timeDist / abs( 1 - (spaceDist / (max(first['End Speed'],.1)))) + speedDist
                        
                        joinedPairs.append([ iterable[0], iterable[1], dist+angle])
                        #print spaceDist, ' ', timeDist, ' ', sizeDist, ' ', speedDist

        joinedPairs.sort(cmpDist)
        self.__data__['Joined Pairs'] = joinedPairs
        tempTracks = []
        tempFrontList = []
        tempBackList = []
        joinedTracks = []
        
        for currentPair in joinedPairs:
            if currentPair[0] not in tempFrontList and currentPair[1] not in tempBackList:
                tempFrontList.append(currentPair[0])
                tempBackList.append(currentPair[1])
                tempTracks.append(currentPair)
        
        joinedTracks = []

        tempTracks.sort(cmpFirstElement)
        
        while tempTracks:
            tempList = []
            tempTrackTwo = list(tempTracks)
            for counter in range(len(tempTrackTwo)):
                if not tempList:
                    tempList.append(tempTrackTwo[counter][0])
                    tempList.append(tempTrackTwo[counter][1])
                    tempTracks.remove(tempTrackTwo[counter])   
                elif tempTrackTwo[counter][0] in tempList:
                    tempList.append(tempTrackTwo[counter][1])
                    tempTracks.remove(tempTrackTwo[counter])

            joinedTracks.append(tempList)

        tempList = [] 
        for joined_track in joinedTracks:
                for segment in joined_track:
                    tempList.append(segment)

        for segment in self.__data__['Segment Info']:
            if segment not in tempList:
                joinedTracks.append([segment])

        joinedTracks.sort(cmpFirstElement)
        joinedTracks = dict(enumerate(joinedTracks,1))
        #print joinedTracks

        for index in joinedTracks:
            trackList = joinedTracks[index]
            start = self.__data__['Segment Info'][trackList[0]]['Start Frame']
            end = self.__data__['Segment Info'][trackList[-1]]['Active Frames'] + \
                  self.__data__['Segment Info'][trackList[-1]]['Start Frame']
            size = 0.0
            speed = 0.0
            distance = 0.0
            frames = 0
            for counter in range(len(trackList)):
                current = self.__data__['Segment Info'][trackList[counter]]
                size += current['Average Area']
                speed += current['Speed']
                distance += current['Distance']
                frames += current['Active Frames']
                if counter > 0:
                    previous = self.__data__['Segment Info'][trackList[counter-1]]
                    distance += sqrt( (current['Start X'] - previous['End X'])**2 + (current['Start Y'] - previous['End Y'])**2 )
                    
            size /= len(trackList)
            speed /= len(trackList)
            
            joinedTracks[index] = { 'Tracks':trackList, 'Start Frame':start, 'End Frame':end, 'Total Frames':frames,\
                                    'Average Area':size, 'Speed':speed, 'Distance':distance,
                                    'Category':self.getObjectCategory(self.__data__['Segment Info'][trackList[counter]])}
        
        good_tracks = {}
        count = 1
        for i in joinedTracks:
            if joinedTracks[i]['Total Frames']>=20 or joinedTracks[i]['Speed'] > .8 and joinedTracks[i]['Distance'] > 0:
                good_tracks[count] = joinedTracks[i]
                count+=1

        for index in good_tracks:
            for segID in good_tracks[index]['Tracks']:
                self.__data__['Segment Info'][segID]['Joined ID'] = index
        
        self.__data__['Joined Tracks'] = good_tracks

        activityData = {'Small':{'Total Distance':0, 'Total Time':0, 'Occurance':0, 'Average Speed':0},\
                        'Medium':{'Total Distance':0, 'Total Time':0, 'Occurance':0, 'Average Speed':0},\
                        'Large':{'Total Distance':0, 'Total Time':0, 'Occurance':0, 'Average Speed':0},\
                        'Fast':{'Total Distance':0, 'Total Time':0, 'Occurance':0, 'Average Speed':0}}        

        for index in good_tracks:
            if good_tracks[index]['Total Frames'] > 29:
                activityData[joinedTracks[index]['Category']]['Average Speed'] += joinedTracks[index]['Speed']
                activityData[joinedTracks[index]['Category']]['Total Distance'] += joinedTracks[index]['Distance']
                activityData[joinedTracks[index]['Category']]['Total Time'] += joinedTracks[index]['Total Frames']
                activityData[joinedTracks[index]['Category']]['Occurance'] += 1

        for category in activityData:
            current = activityData[category]
            if current['Occurance']:
                current['Average Distance'] = current['Total Distance'] / current['Occurance']
                current['Average Time'] = current['Total Time'] / current['Occurance']
                current['Average Speed'] /= current['Occurance']
            else:
                current['Average Distance'] = 0
                current['Average Time'] = 0

                
        self.__data__['Activity Info'] = activityData
            
            
        
        print "Done."
