#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------------------------------------
# 
# 
# 
#-----------------------------------------------------------------------------------------------------------
"""
This code is an attempt to replicate the Murray et al. 2018 study on sex differences in temporal motion detection thresholds.

Murray, S. O., Schallmo, M.-P., Kolodny, T., Millin, R., Kale, A., Thomas, P., Rammsayer, T. H., et al. (2018). 
Sex Differences in Visual Motion Processing. Current Biology, 28(17), 2794-2799.
Retrieved from http://dx.doi.org/10.1016/j.cub.2018.06.014
"""

#-----------------------------------------------------------------------------------------------------------
# Initialize
#-----------------------------------------------------------------------------------------------------------

# import external packages
from __future__ import absolute_import, division, print_function
from psychopy import core, visual, gui, data, event, sound
from psychopy.tools.filetools import fromFile, toFile
from psychopy.visual import ShapeStim
from psychopy.hardware import keyboard
import time, numpy
import os  # handy system and path functions

# user-defined parameters
import motion_temporal_threshold_params as params

# Set up hardware
kb = keyboard.Keyboard()

#-----------------------------------------------------------------------------------------------------------
# Define helper functions
#-----------------------------------------------------------------------------------------------------------

def rand_unif_int(min, max):
    # Force min >= 0 and max >= 0
    if min < 0:
        min = 0
    if max < 0:
        max = 0
    return (min + numpy.random.random()*(max-min))
    
def calculate_stim_duration(frames, frame_rate_hz):
    if frame_rate_hz == 0:
        frame_rate_hz = frameRate
    return (frames/frame_rate_hz)
    
def write_trial_data_header():
    dataFile.write('observer,gender')
    dataFile.write(',trial_n, motion_dir,grating_ori,key_resp,grating_deg')
    dataFile.write(',contrast,spf,tf_hz,stim_secs')
    dataFile.write(',frame_rate_hz,frameDur,correct,rt')
    dataFile.write(',grating_start,grating_end\n')

def write_trial_data_to_file():
    dataFile.write('%s,%s' % (expInfo['observer'], expInfo['gender']))
    dataFile.write(',%i,%i,%s,%s,%.2f' % (n_trials,this_dir,this_dir_str, thisKey, this_grating_degree))
    dataFile.write(',%.3f,%.3f,%.3f,%.9f' % (this_max_contrast, this_spf, this_tf, this_stim_secs))
    dataFile.write(',%.9f,%.3f,%.2f, %.3f' % (frameRate, frameDur, thisResp, rt))
    dataFile.write(',%.3f,%.3f\n' % (start_resp_time, clock.getTime()))
    
def calculate_contrast():
    if params.contrast_mod_type == 'fixed_trapezoidal':
        ramp_up_secs = frameDur 
        ramp_down_secs = frameDur 
        secs_passed = clock.getTime()-start_time
        if this_stim_secs >= 3*frameDur:
            if 0 <=secs_passed < ramp_up_secs:
                this_contr =  0.5 * this_max_contrast
            elif this_stim_secs >= secs_passed > this_stim_secs-ramp_down_secs:
                this_contr = 0.5*this_max_contrast
            else:
                this_contr = this_max_contrast
        else:
            this_contr = this_max_contrast
    elif params.contrast_mod_type == 'variable_triangular': # linear ramp up for half of this_stim_secs, then ramp down
        secs_passed = clock.getTime()-start_time
        if secs_passed <= this_stim_secs * 0.5: # first half
            this_contr = (secs_passed/(this_stim_secs*0.5))*this_max_contrast
        else: 
            this_contr = (this_stim_secs - secs_passed )/(this_stim_secs * 0.5)*this_max_contrast
    else:
        this_contr = this_condition['max_contr']
        
    # Sanity check on this_contr to keep in [0.1]
    if this_contr > 1:
        this_contr = 1
    elif this_contr < 0:
        this_contr = 0
        
    return(this_contr)
    
def show_practice_trial():
    win.flip()
    # randomly set motion direction of grating on each trial
    if (round(numpy.random.random())) > 0.5:
        this_dir = +1 # leftward
        this_dir_str='left'
    else:
        this_dir = -1 # rightward
        this_dir_str='right'
    
    this_stim_secs = .5
    this_grating_degree = 4
    this_spf = 1.2
    keep_going = 1
    
    pr_grating = visual.GratingStim(
        win=win, name='grating_murray',units='deg', 
        tex='sin', mask='gauss',
        ori=params.grating_ori, pos=(0, 0), size=this_grating_degree, sf=this_spf, phase=0,
        color=0, colorSpace='rgb', opacity=1, blendmode='avg',
        texRes=128, interpolate=True, depth=0.0)
    
    # fixation until keypress
    fixation.draw()
    win.flip()
    event.waitKeys()
    win.flip()
    
    # ISI
    core.wait(params.fixation_grating_isi)
    
    # show grating
    start_time = clock.getTime()
    while keep_going:
        secs_from_start = (start_time - clock.getTime())
        pr_grating.phase = this_dir*(secs_from_start/params.cyc_secs)
        
        # Modulate contrast
        this_contr = .98
        pr_grating.color = this_contr
    
        # Draw next grating component
        pr_grating.draw()
        win.flip()
        grating_start = clock.getTime()
    
        # Start collecting responses
        thisResp = None
    
        # Is stimulus presentation time over?
        if (clock.getTime()-start_time > this_stim_secs):
            win.flip()
            keep_going = False 
            
        # check for quit (typically the Esc key)
        if kb.getKeys(keyList=["escape"]):
            thisResp = 0
            rt = 0
                    
            print("Exiting program.")
            core.quit()
    
    # clear screen, get response
    if params.show_response_frame:
        respond.draw()
        win.flip()
    start_resp_time = clock.getTime()
    
    # Show response fixation
    while thisResp is None:
        allKeys = event.waitKeys()
        rt = clock.getTime() - start_resp_time
        for thisKey in allKeys:
            if ((thisKey == 'left' and this_dir == -1) or
                (thisKey == 'right' and this_dir == +1)):
                thisResp = 0 # incorrect
            elif ((thisKey == 'left' and this_dir == +1) or
                (thisKey == 'right' and this_dir == -1)):
                thisResp = 1  # correct
                
                # Feedback
                highA.play(loops=-1)    # Only first plays?
                donut.draw()            # Try visual feedback for now
            elif thisKey in ['q', 'escape']:
                test = False
                core.quit()  # abort experiment
    #-----------------------------------------------------------------------------------------------------------
    
    win.flip()
    if (thisResp == 0):
        instructionsIncorrect.draw()
    else:
        instructionsCorrect.draw()
    win.flip()
    
    # wait
    core.wait(1)
#-----------------------------------------------------------------------------------------------------------

#dataFile.write('motion_dir,grating_ori,key_resp,grating_deg,contrast,spf,tf_hz,show_frames,frame_rate_hz,show_secs,correct,rt,grating_start,grating_end\n')

# Clock variables
clock = core.Clock()
countDown = core.CountdownTimer()

# sound
highA = sound.Sound('A', octave=4, sampleRate=44100, secs=0.2, stereo=True, loops=-1)
highA.setVolume(0.5)

# create window and stimuli
win = visual.Window([params.window_pix_h, params.window_pix_v], allowGUI=False, monitor=params.monitor_name, units='deg')
fixation = visual.GratingStim(win, color='black', tex=None, mask='circle', size=0.2)
respond = visual.GratingStim(win, color='white', tex=None, mask='circle', size=0.3)

pr_grating = visual.GratingStim(
    win=win, name='grating_murray',units='deg', 
    tex='sin', mask='gauss',
    ori=params.grating_ori, pos=(0, 0), size=params.grating_deg, sf=params.spf, phase=0,
    color=[params.max_contr, params.max_contr, params.max_contr], colorSpace='rgb', opacity=1, blendmode='avg',
    texRes=128, interpolate=True, depth=0.0)
    
# `donut` has a true hole, using two loops of vertices:
donutVert = [[(-params.donut_outer_rad,-params.donut_outer_rad),(-params.donut_outer_rad,params.donut_outer_rad),(params.donut_outer_rad,params.donut_outer_rad),(params.donut_outer_rad,-params.donut_outer_rad)],
[(-params.donut_inner_rad,-params.donut_inner_rad),(-params.donut_inner_rad,params.donut_inner_rad),(params.donut_inner_rad,params.donut_inner_rad),(params.donut_inner_rad,-params.donut_inner_rad)]]
donut = ShapeStim(win, vertices=donutVert, fillColor=params.donut_color, lineWidth=0, size=.75, pos=(0, 0))

# text messages
experimenter  = visual.TextStim(win, pos=[0, 0], 
    text = 'This is the Motion Duration Threshold Study.\n\nPress SPACE bar to continue.')
welcome  = visual.TextStim(win, pos=[0, 0], 
    text = 'Welcome to the motion duration threshold study.\n\nPress SPACE bar to continue.')
instructions1 = visual.TextStim(win, pos=[0, 0], text = 'You will see a small patch of black and white stripes moving leftward or rightward.')
instructions2 = visual.TextStim(win, pos=[0, 0], text = 'Your goal is to detect whether the patch is moving to the left or the right.\n\nPress SPACE bar to continue.')
instructions3a = visual.TextStim(win, pos=[0, + 3],
    text='When the small black box appears, look at it.\n\nPress SPACE bar to continue.')
instructions3b = visual.TextStim(win, pos=[0, -3],
    text="Then press one of the arrow keys or sapce bar to start the display.\n\nPress SPACE bar to continue.")
instructions4 = visual.TextStim(win, pos=[0, 0], text = 'Once the white dot appears, press the left arrow key if you see leftward motion and the right arrow key if you see rightward motion.\n\nIf you are not sure, just guess.\n\nYour goal is accuracy, not speed.\n\nPress SPACE bar to continue.')
instructions5 = visual.TextStim(win, pos=[0, 0], text = 'To try some easy practice trials, hit any key to show the black fixation dot, look at the dot, and then press any key again to show the display.\n\nPress SPACE bar to continue.')
instructionsIncorrect = visual.TextStim(win, pos=[0, 0], text = 'Almost. Make sure to pay close attention.')
instructionsCorrect = visual.TextStim(win, pos=[0, 0], text = 'Awesome.')
instructions6 = visual.TextStim(win, pos=[0, 0], text = 'Do you have any questions? If not, press SPACE bar to get started!')
thanksMsg = visual.TextStim(win, pos=[0, 0],text="You're done! You can contact the researcher outside the room and feel free to have a break if you need!")


#-----------------------------------------------------------------------------------------------------------
# Start experiment
#-----------------------------------------------------------------------------------------------------------

# experimenter
experimenter.draw()
win.flip()
event.waitKeys()
win.flip()

# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

# Store info about the experiment session
psychopyVersion = '3.2.4'
expName = 'motion_temporal_threshold'  # from the Builder filename that created this script
# expInfo['date'] = data.getDateStr()  # add a simple timestamp
# expInfo['expName'] = expName
# expInfo['psychopyVersion'] = psychopyVersion

# enter participant info
try:  # try to get a previous parameters file
    expInfo = fromFile('lastParams.pickle')
except:  # if not there then use a default set
    expInfo = {'gender':'','observer':time.strftime("%Y-%m-%d-%H%M%S")}

# get the real frame rate of the monitor
frameRate= win.getActualFrameRate()
if frameRate != None:
    frameDur = 1.0 / round(frameRate)
else:
    frameDur = 1.0 / frame_rate_hz  # could not measure, so guess
    
# present a dialog to change params
dlg = gui.DlgFromDict(expInfo, title='Motion Temporal threshold', fixed=['date'])
if dlg.OK:
    toFile('lastParams.pickle', expInfo)  # save params to file for next time
else:
    core.quit()  # the user hit cancel so exit

# make an output text file to save data
fileName = _thisDir+os.sep+'csv'+os.sep+ '%s_%s' % (expInfo['observer'] ,expName)
dataFile = open(fileName + '.csv', 'w')
write_trial_data_header()

# welcome
welcome.draw()
win.flip()
event.waitKeys()
win.flip()

# instructions
instructions1.draw()
win.flip()
event.waitKeys()

instructions2.draw()
win.flip()
event.waitKeys()

instructions3a.draw()
instructions3b.draw()
fixation.draw()
win.flip()
event.waitKeys()

instructions4.draw()
win.flip()
event.waitKeys()

instructions5.draw()
win.flip()
event.waitKeys()

#-----------------------------------------------------------------------------------------------------------
# Show sample 1

# randomly set motion direction of grating on each trial
#if (round(numpy.random.random())) > 0.5:
#    this_dir = +1 # leftward
#    this_dir_str='left'
#else:
#    this_dir = -1 # rightward
#    this_dir_str='right'
#
#this_stim_secs = .5
#this_grating_degree = 4
#this_spf = 1.2
#keep_going = 1
#
#pr_grating = visual.GratingStim(
#    win=win, name='grating_murray',units='deg', 
#    tex='sin', mask='gauss',
#    ori=params.grating_ori, pos=(0, 0), size=this_grating_degree, sf=this_spf, phase=0,
#    color=0, colorSpace='rgb', opacity=1, blendmode='avg',
#    texRes=128, interpolate=True, depth=0.0)
#
#start_time = clock.getTime()
#while keep_going:
#    secs_from_start = (start_time - clock.getTime())
#    pr_grating.phase = this_dir*(secs_from_start/params.cyc_secs)
#    
#    # Modulate contrast
#    this_contr = .98
#    pr_grating.color = this_contr
#
#    # Draw next grating component
#    pr_grating.draw()
#    win.flip()
#    grating_start = clock.getTime()
#
#    # Start collecting responses
#    thisResp = None
#
#    # Is stimulus presentation time over?
#    if (clock.getTime()-start_time > this_stim_secs):
#        win.flip()
#        keep_going = False 
#        
#    # check for quit (typically the Esc key)
#    if kb.getKeys(keyList=["escape"]):
#        thisResp = 0
#        rt = 0
#                
#        print("Exiting program.")
#        core.quit()
#
# clear screen get response
#if params.show_response_frame:
#    respond.draw()
#    win.flip()
#start_resp_time = clock.getTime()
#
# Show response fixation
#while thisResp is None:
#    allKeys = event.waitKeys()
#    rt = clock.getTime() - start_resp_time
#    for thisKey in allKeys:
#        if ((thisKey == 'left' and this_dir == -1) or
#            (thisKey == 'right' and this_dir == +1)):
#            thisResp = 0 # incorrect
#        elif ((thisKey == 'left' and this_dir == +1) or
#            (thisKey == 'right' and this_dir == -1)):
#            thisResp = 1  # correct
#            
#            # Feedback
#            highA.play(loops=-1)    # Only first plays?
#            donut.draw()            # Try visual feedback for now
#        elif thisKey in ['q', 'escape']:
#            test = False
#            core.quit()  # abort experiment
#-----------------------------------------------------------------------------------------------------------

show_practice_trial()
show_practice_trial()
show_practice_trial()
show_practice_trial()
show_practice_trial()
show_practice_trial()
show_practice_trial()
show_practice_trial()
show_practice_trial()
show_practice_trial()

instructions6.draw()
win.flip()
event.waitKeys()

# Start staircase
intru_break = visual.TextStim(win, pos=[0, 0], text = 'Press SPACE bar to continue.')

current_run=0
total_run=range(4)
for current_run in total_run:
    # create the staircase handler
    if params.staircase_style == 'QUEST':
        staircase = data.MultiStairHandler(stairType='QUEST', conditions=params.conditions_QUEST,  nTrials=params.staircase_ntrials)
    else:
        staircase = data.MultiStairHandler(stairType='simple', conditions=params.conditions_simple, nTrials=params.staircase_ntrials)
    print('Created staircase: %s' % params.staircase_style)
    if current_run<3:
        intru_break.draw()
        win.flip()
        event.waitKeys()
    current_run=current_run+1
    n_trials = 0
    for this_stim_secs, this_condition in staircase:
        
        # Print trial number, condition info to console
        n_trials += 1
        print('trial:', str(n_trials), 'condition: ' + this_condition['label'] + " | " + 'stim_secs: ' + str(this_stim_secs))
        
        # Initialize grating parameters for this condition
        this_max_contrast = this_condition['max_contr']
        this_grating_degree = this_condition['grating_deg']
        this_tf = this_condition['tf']
        this_spf = this_condition['spf']
    
        # randomly set motion direction of grating on each trial
        if (round(numpy.random.random())) > 0.5:
            this_dir = +1 # leftward
            this_dir_str='left'
        else:
            this_dir = -1 # rightward
            this_dir_str='right'
        
        # draw initial grating
        pr_grating = visual.GratingStim(
            win=win, name='grating_murray',units='deg', 
            tex='sin', mask=this_condition['mask_type'],
            ori=params.grating_ori, pos=(0, 0), size=this_grating_degree, sf=this_spf, phase=0,
            color=0, colorSpace='rgb', opacity=1, blendmode='avg',
            texRes=128, interpolate=True, depth=0.0)
        
        # Show fixation until key press
        fixation.draw()
        win.flip()
        event.waitKeys()
        win.flip()
        
        # ISI (uniform within [isi_min, isi_max])
        core.wait(params.fixation_grating_isi)
        
        # draw grating
        keep_going = True
        start_time = clock.getTime()
        while keep_going:
            secs_from_start = (start_time - clock.getTime())
            pr_grating.phase = this_dir*(secs_from_start/params.cyc_secs)
            
            # Modulate contrast
            this_contr = calculate_contrast()
            pr_grating.color = this_contr
    
            # Draw next grating component
            pr_grating.draw()
            win.flip()
            grating_start = clock.getTime()
    
            # Start collecting responses
            thisResp = None
    
            # Is stimulus presentation time over?
            if (clock.getTime()-start_time > this_stim_secs):
                win.flip()
                keep_going = False 
                
            # check for quit (typically the Esc key)
            if kb.getKeys(keyList=["escape"]):
                thisResp = 0
                rt = 0
                
                print("Saving data.")
                write_trial_data_to_file()
                
                print("Exiting program.")
                core.quit()
    
        # clear screen get response
        if params.show_response_frame:
            respond.draw()
            win.flip()
        start_resp_time = clock.getTime()
        
        # Show response fixation
        while thisResp is None:
            allKeys = event.waitKeys()
            rt = clock.getTime() - start_resp_time
            for thisKey in allKeys:
                if ((thisKey == 'left' and this_dir == -1) or
                    (thisKey == 'right' and this_dir == +1)):
                    thisResp = 0 # incorrect
                elif ((thisKey == 'left' and this_dir == +1) or
                    (thisKey == 'right' and this_dir == -1)):
                    thisResp = 1  # correct
                    
                    # Feedback
                    highA.play(loops=-1)    # Only first plays?
                    donut.draw()            # Try visual feedback for now
                    win.flip()
                elif thisKey in ['q', 'escape']:
                    test = False
                    core.quit()  # abort experiment
            event.clearEvents('mouse')  # only really needed for pygame windows
    
        # add the data to the staircase so it can calculate the next level
        staircase.addResponse(thisResp)
        
        # Write data to file
        write_trial_data_to_file()
    
        # Clear screen and ITI
        win.flip()
        # core.wait(rand_unif_int(params.iti_min, params.iti_max))
        core.wait(params.fixation_grating_isi)
#-----------------------------------------------------------------------------------------------------------
thanksMsg.draw()
win.flip()
event.waitKeys()
#-----------------------------------------------------------------------------------------------------------
# Save data and clean-up
#-----------------------------------------------------------------------------------------------------------

# staircase has ended
dataFile.close()
staircase.saveAsPickle(fileName)  # special python data file to save all the info

# give some output to user
if params.staircase_style == 'simple':
    print('reversals:')
    print(staircase.reversalIntensities)
    print('mean of final 5 reversals = %.3f' % numpy.average(staircase.reversalIntensities[-5:]))

# clean-up
win.close()
core.quit()
