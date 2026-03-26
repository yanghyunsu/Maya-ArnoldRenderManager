import os
import re  # used in validate check_sequence()
import maya.cmds as cmds
import maya.mel as mel

class ArnoldRenderManager:
    def __init__(self):
        self.window_name = "arnoldRenderManagerUI"
        self.is_rendering = False
        
        # Arnold AOV options
        self.arnold_aovs = ['beauty', 'diffuse', 'specular', 'emission', 'sss', 'transmission', 'ao', 'Z']
        
        # Store checkbox references
        self.aov_checkboxes = {}
        
    def get_timeline_range(self):
        start = int(cmds.playbackOptions(q=True, minTime=True))
        end = int(cmds.playbackOptions(q=True, maxTime=True))
        return start, end
    
    def get_default_images_path(self):
        workspace = cmds.workspace(q=True, rootDirectory=True)
        images_folder = os.path.join(workspace, "images")
        images_folder = os.path.normpath(images_folder)
        
        if not os.path.exists(images_folder):
            try:
                os.makedirs(images_folder)
            except:
                pass
        
        return images_folder
    
    def get_scene_cameras(self):
        cameras = cmds.listCameras()
        return cameras
    
    def setup_arnold_aovs(self, aovs):
        if not cmds.pluginInfo('mtoa', query=True, loaded=True):
            try:
                cmds.loadPlugin('mtoa')
            except:
                return False
        
        try:
            import mtoa.aovs as aovs_module
        except:
            return False
        
        existing_aovs = cmds.ls(type='aiAOV')
        if existing_aovs:
            cmds.delete(existing_aovs)
        
        for aov in aovs:
            if aov == 'beauty':
                continue
            
            aov_map = {
                'diffuse': 'diffuse',
                'specular': 'specular',
                'emission': 'emission',
                'sss': 'sss',
                'transmission': 'transmission',
                'ao': 'ao',
                'Z': 'Z'
            }
            
            if aov in aov_map:
                try:
                    aovs_module.AOVInterface().addAOV(aov_map[aov])
                except:
                    pass
        
        return True
    
    def get_selected_aovs(self):
        # Get list of checked AOVs for rendering
        selected = []
        for aov, checkbox in self.aov_checkboxes.items():
            if cmds.checkBox(checkbox, q=True, value=True):
                selected.append(aov)
        return selected
        
    def create_ui(self):
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        
        timeline_start, timeline_end = self.get_timeline_range()
        default_images = self.get_default_images_path()
        
        cmds.window(self.window_name, title="Arnold Render Manager", 
                   widthHeight=(520, 550), sizeable=False)
        
        self.main_layout = cmds.columnLayout(adjustableColumn=True, 
                                            columnAttach=('both', 10),
                                            rowSpacing=8)
        
        cmds.separator(height=5)
        
        # === TITLE ===
        cmds.text(label="ARNOLD RENDER MANAGER", font="boldLabelFont", 
                 align='center', backgroundColor=(0.3, 0.3, 0.4), height=30)
        
        cmds.separator(height=10)
        
        # === RENDER SEQUENCE SECTION ===
        cmds.text(label="RENDER SEQUENCE", font="boldLabelFont", 
                 align='left', backgroundColor=(0.4, 0.4, 0.5), height=25)
        
        # Camera
        cmds.rowLayout(numberOfColumns=2, 
                      columnWidth2=(90, 380),
                      columnAttach=[(1, 'left', 0), (2, 'both', 5)])
        cmds.text(label="Camera:", align='right')
        self.camera_menu = cmds.optionMenu()
        cameras = self.get_scene_cameras()
        for cam in cameras:
            cmds.menuItem(label=cam)
        cmds.setParent(self.main_layout)
        
        # Output path with browse
        cmds.rowLayout(numberOfColumns=3, 
                      columnWidth3=(90, 330, 60),
                      columnAttach=[(1, 'left', 0), (2, 'both', 5), (3, 'left', 0)])
        cmds.text(label="Output Path:", align='right')
        self.output_path_field = cmds.textField(text=default_images)
        cmds.button(label="Browse", width=60, command=lambda x: self.browse_output_path())
        cmds.setParent(self.main_layout)
        
        # File name
        cmds.rowLayout(numberOfColumns=2, 
                      columnWidth2=(90, 380),
                      columnAttach=[(1, 'left', 0), (2, 'both', 5)])
        cmds.text(label="File Name:", align='right')
        self.file_name_field = cmds.textField(text="render")
        cmds.setParent(self.main_layout)
        
        # Frame range
        cmds.rowLayout(numberOfColumns=6,
                      columnWidth6=(90, 60, 30, 60, 20, 70),
                      columnAttach=[(1, 'left', 0), (2, 'both', 2), (3, 'both', 2), 
                                   (4, 'both', 2), (5, 'both', 2), (6, 'left', 2)])
        cmds.text(label="Frames:", align='right')
        self.gen_start_frame = cmds.intField(value=timeline_start)
        cmds.text(label="to", align='center')
        self.gen_end_frame = cmds.intField(value=timeline_end)
        cmds.text(label="")
        cmds.button(label="Timeline", width=70,
                   command=lambda x: self.use_timeline_range_gen(),
                   backgroundColor=(0.35, 0.35, 0.4))
        cmds.setParent(self.main_layout)
        
        # Resolution
        cmds.rowLayout(numberOfColumns=5,
                      columnWidth5=(90, 70, 15, 70, 100),
                      columnAttach=[(1, 'left', 0), (2, 'both', 2), (3, 'both', 2), 
                                   (4, 'both', 2), (5, 'left', 2)])
        cmds.text(label="Resolution:", align='right')
        self.width_field = cmds.intField(value=1920)
        cmds.text(label="x", align='center')
        self.height_field = cmds.intField(value=1080)
        cmds.button(label="Current", width=100,
                   command=lambda x: self.use_render_resolution(),
                   backgroundColor=(0.35, 0.35, 0.4))
        cmds.setParent(self.main_layout)
        
        # Render AOVs
        cmds.separator(height=5)
        cmds.text(label="Render AOVs:", align='left', font="boldLabelFont")
        cmds.frameLayout(labelVisible=False, 
                        marginWidth=5, marginHeight=5,
                        backgroundColor=(0.25, 0.25, 0.25))
        
        cmds.rowColumnLayout(numberOfColumns=4, 
                            columnWidth=[(1, 120), (2, 120), (3, 120), (4, 120)])
        
        for aov in self.arnold_aovs:
            default_value = True
            enable_value = False if aov == 'beauty' else True
            
            self.aov_checkboxes[aov] = cmds.checkBox(
                label=aov.upper(),
                value=default_value,
                enable=enable_value
            )
        
        cmds.setParent(self.main_layout)
        cmds.setParent(self.main_layout)
        
        # Progress bar
        cmds.separator(height=5)
        self.progress_bar = cmds.progressBar(maxValue=100, width=500, height=25, visible=False)
        
        # Render buttons (START + STOP)
        cmds.separator(height=5)
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(250, 250),
                      columnAttach=[(1, 'both', 2), (2, 'both', 2)])
        self.render_button = cmds.button(label="START RENDER", height=40,
                   backgroundColor=(0.4, 0.4, 0.5),
                   command=lambda x: self.start_render())
        self.stop_button = cmds.button(label="STOP RENDER", height=40,
                   backgroundColor=(0.5, 0.3, 0.3),
                   enable=False,
                   command=lambda x: self.stop_render())
        cmds.setParent(self.main_layout)
        
        cmds.separator(height=15)
        
        # === VALIDATION SECTION ===
        cmds.text(label="VALIDATE SEQUENCE", font="boldLabelFont", 
                 align='left', backgroundColor=(0.5, 0.4, 0.4), height=25)
        
        # Validation path with browse
        cmds.rowLayout(numberOfColumns=3, 
                      columnWidth3=(90, 330, 60),
                      columnAttach=[(1, 'left', 0), (2, 'both', 5), (3, 'left', 0)])
        cmds.text(label="Sequence Path:", align='right')
        self.validation_path_field = cmds.textField(text=default_images)
        cmds.button(label="Browse", width=60, command=lambda x: self.browse_validation_path())
        cmds.setParent(self.main_layout)
        
        # Frame range
        cmds.rowLayout(numberOfColumns=6,
                      columnWidth6=(90, 60, 30, 60, 20, 70),
                      columnAttach=[(1, 'left', 0), (2, 'both', 2), (3, 'both', 2), 
                                   (4, 'both', 2), (5, 'both', 2), (6, 'left', 2)])
        cmds.text(label="Frames:", align='right')
        self.start_frame = cmds.intField(value=timeline_start)
        cmds.text(label="to", align='center')
        self.end_frame = cmds.intField(value=timeline_end)
        cmds.text(label="")
        cmds.button(label="Timeline", width=70,
                   command=lambda x: self.use_timeline_range_val(),
                   backgroundColor=(0.35, 0.35, 0.4))
        cmds.setParent(self.main_layout)
        
        # Validate button
        cmds.separator(height=5)
        cmds.button(label="VALIDATE RENDERS", height=40,
                   backgroundColor=(0.5, 0.4, 0.4),
                   command=lambda x: self.validate())
        
        cmds.separator(height=10)
        
        cmds.showWindow()
    
    def browse_output_path(self):
        # Browse for output path - starts from current path 
        current_path = cmds.textField(self.output_path_field, q=True, text=True)
        
        if os.path.exists(current_path):
            start_dir = current_path
        else:
            start_dir = self.get_default_images_path()
        
        folder = cmds.fileDialog2(fileMode=3, 
                                 caption="Select Output Folder",
                                 startingDirectory=start_dir)
        if folder:
            cmds.textField(self.output_path_field, edit=True, text=os.path.normpath(folder[0]))
    
    def browse_validation_path(self):
        # Browse for validation path - starts from current path 
        current_path = cmds.textField(self.validation_path_field, q=True, text=True)
        
        if os.path.exists(current_path):
            start_dir = current_path
        else:
            start_dir = self.get_default_images_path()
        
        folder = cmds.fileDialog2(fileMode=3, 
                                 caption="Select Sequence Folder",
                                 startingDirectory=start_dir)
        if folder:
            cmds.textField(self.validation_path_field, edit=True, text=os.path.normpath(folder[0]))
    
    def use_render_resolution(self):
        width = cmds.getAttr('defaultResolution.width')
        height = cmds.getAttr('defaultResolution.height')
        cmds.intField(self.width_field, edit=True, value=width)
        cmds.intField(self.height_field, edit=True, value=height)
    
    def use_timeline_range_gen(self):
        start, end = self.get_timeline_range()
        cmds.intField(self.gen_start_frame, edit=True, value=start)
        cmds.intField(self.gen_end_frame, edit=True, value=end)
    
    def use_timeline_range_val(self):
        start, end = self.get_timeline_range()
        cmds.intField(self.start_frame, edit=True, value=start)
        cmds.intField(self.end_frame, edit=True, value=end)
    
    def stop_render(self):
        # Stop rendering
        self.is_rendering = False
        cmds.button(self.render_button, edit=True, enable=True)
        cmds.button(self.stop_button, edit=True, enable=False)
        cmds.progressBar(self.progress_bar, edit=True, visible=False)
    
    def start_render(self):
        current_file = cmds.file(q=True, sceneName=True)
        if not current_file:
            cmds.confirmDialog(title="Error", message="Please save your scene first!", button=['OK'])
            return
        
        cmds.file(save=True)
        
        output_folder = cmds.textField(self.output_path_field, q=True, text=True)
        file_name = cmds.textField(self.file_name_field, q=True, text=True)
        start = cmds.intField(self.gen_start_frame, q=True, value=True)
        end = cmds.intField(self.gen_end_frame, q=True, value=True)
        width = cmds.intField(self.width_field, q=True, value=True)
        height = cmds.intField(self.height_field, q=True, value=True)
        camera = cmds.optionMenu(self.camera_menu, q=True, value=True)
        
        aovs = self.get_selected_aovs()
        
        if not output_folder:
            cmds.confirmDialog(title="Error", message="Please select output folder!", button=['OK'])
            return
        
        output_folder = os.path.normpath(output_folder)
        
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder)
            except Exception as e:
                cmds.confirmDialog(title="Error", message=f"Cannot create folder:\n{str(e)}", button=['OK'])
                return
        
        # Set camera renderable
        all_cameras = cmds.listCameras()
        for cam in all_cameras:
            cmds.setAttr(f"{cam}.renderable", 0)
        
        camera_shape = camera
        if cmds.objectType(camera) != 'camera':
            shapes = cmds.listRelatives(camera, shapes=True, type='camera')
            if shapes:
                camera_shape = shapes[0]
        
        cmds.setAttr(f"{camera_shape}.renderable", 1)
        
        # Setup Arnold
        cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
        self.setup_arnold_aovs(aovs)
        
        # Set render settings
        cmds.setAttr('defaultRenderGlobals.startFrame', start)
        cmds.setAttr('defaultRenderGlobals.endFrame', end)
        cmds.setAttr('defaultResolution.width', width)
        cmds.setAttr('defaultResolution.height', height)
        
        # Set output path
        output_path = os.path.join(output_folder, file_name)
        output_path = output_path.replace("\\", "/")
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', output_path, type='string')
        cmds.setAttr('defaultRenderGlobals.imageFormat', 40)
        cmds.setAttr('defaultRenderGlobals.outFormatControl', 0)
        cmds.setAttr('defaultRenderGlobals.animation', 1)
        cmds.setAttr('defaultRenderGlobals.putFrameBeforeExt', 1)
        cmds.setAttr('defaultRenderGlobals.extensionPadding', 4)
        
        if not cmds.objExists('defaultArnoldDriver'):
            cmds.createNode('aiAOVDriver', name='defaultArnoldDriver')
        cmds.setAttr('defaultArnoldDriver.aiTranslator', 'exr', type='string')
        cmds.setAttr('defaultArnoldDriver.mergeAOVs', 1)
        cmds.setAttr('defaultArnoldDriver.exrCompression', 3)
        
        cmds.file(save=True)
        
        # UI updates
        cmds.button(self.render_button, edit=True, enable=False)
        cmds.button(self.stop_button, edit=True, enable=True)
        cmds.progressBar(self.progress_bar, edit=True, visible=True, progress=0)
        
        # Auto-fill validation
        cmds.textField(self.validation_path_field, edit=True, text=output_folder)
        cmds.intField(self.start_frame, edit=True, value=start)
        cmds.intField(self.end_frame, edit=True, value=end)
        
        # Store variables
        self._cur_frame = start
        self._end_frame = end
        self._start_val = start
        self._output_folder = output_folder
        self._camera = camera
        
        # Start rendering
        self.is_rendering = True
        self.render_loop()
    
    def render_loop(self):
        if not self.is_rendering:
            self.finish_render()
            return
        
        if self._cur_frame > self._end_frame:
            self.finish_render()
            return

        # Set current frame
        cmds.currentTime(self._cur_frame)
        
        # Set frame range for this single frame
        cmds.setAttr("defaultRenderGlobals.startFrame", self._cur_frame)
        cmds.setAttr("defaultRenderGlobals.endFrame", self._cur_frame)
        
        try:
            mel.eval('renderSequence')
        except Exception as e:
            print(f"Render error on frame {self._cur_frame}: {str(e)}")
        
        # Next frame
        self._cur_frame += 1
        
        # Update progress
        total = float(self._end_frame - self._start_val + 1)
        progress = int(((self._cur_frame - self._start_val) / total) * 100)
        cmds.progressBar(self.progress_bar, edit=True, progress=min(progress, 100))
        
        # Continue loop
        cmds.evalDeferred(self.render_loop)
    
    def finish_render(self):
        self.is_rendering = False
        cmds.progressBar(self.progress_bar, edit=True, progress=100, visible=False)
        cmds.button(self.render_button, edit=True, enable=True)
        cmds.button(self.stop_button, edit=True, enable=False)
        
        # Auto validate
        cmds.evalDeferred(lambda: self.validate())
    
    def validate(self):
        # Validate rendered sequence
        validation_folder = cmds.textField(self.validation_path_field, q=True, text=True)
        start = cmds.intField(self.start_frame, q=True, value=True)
        end = cmds.intField(self.end_frame, q=True, value=True)
        
        # Validation checks
        if not validation_folder:
            cmds.confirmDialog(title="Error", message="No validation path specified!", button=['OK'])
            return
        
        if not os.path.exists(validation_folder):
            cmds.confirmDialog(title="Error", message=f"Folder does not exist!\n{validation_folder}", button=['OK'])
            return
        
        # Perform validation
        result = self.check_sequence(validation_folder, start, end)
        
        # Show in new window
        self.show_validation_window(result)
    
    def show_validation_window(self, report):
        # Show validation report in a new window 
        win_name = "validationReportUI"
        
        if cmds.window(win_name, exists=True):
            cmds.deleteUI(win_name)
        
        cmds.window(win_name, title="Validation Report", widthHeight=(600, 400), sizeable=True)
        
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, 
                                       columnAttach=('both', 10))
        
        cmds.separator(height=5)
        
        # Title
        cmds.text(label="VALIDATION REPORT", font="boldLabelFont", 
                 align='center', backgroundColor=(0.5, 0.4, 0.4), height=30)
        
        cmds.separator(height=10)
        
        # Report text
        cmds.scrollField(text=report, 
                        editable=False,
                        wordWrap=True,
                        font="smallFixedWidthFont",
                        backgroundColor=(0.15, 0.15, 0.15),
                        height=300)
        
        cmds.separator(height=10)
        
        # Close button
        cmds.button(label="CLOSE", height=35,
                   backgroundColor=(0.4, 0.4, 0.5),
                   command=lambda x: cmds.deleteUI(win_name))
        
        cmds.separator(height=5)
        
        cmds.showWindow(win_name)
    
    def is_valid_exr(self, file_path):
        # Check if EXR file is valid by trying to read it
        try:
            # Try with OpenEXR first (more reliable)
            try:
                import OpenEXR
                import Imath
                
                exr_file = OpenEXR.InputFile(file_path)
                header = exr_file.header()
                
                # Check if it has channels
                channels = header['channels']
                if not channels or len(channels) == 0:
                    return False, "No channels found"
                
                # Try to read a small amount of data to verify it's not corrupt
                dw = header['dataWindow']
                width = dw.max.x - dw.min.x + 1
                height = dw.max.y - dw.min.y + 1
                
                # If dimensions are invalid
                if width <= 0 or height <= 0:
                    return False, f"Invalid dimensions: {width}x{height}"
                
                # Try to read first channel
                channel_name = list(channels.keys())[0]
                pt = Imath.PixelType(Imath.PixelType.FLOAT)
                
                # Try to read just one scanline to verify data integrity
                try:
                    exr_file.channel(channel_name, pt)
                except:
                    return False, "Cannot read channel data"
                
                return True, "OK"
                
            except ImportError:
                # Fallback: Use basic file checks
                file_size = os.path.getsize(file_path)
                
                # Check minimum size (EXR header is ~100 bytes minimum)
                if file_size < 100:
                    return False, f"File too small: {file_size} bytes"
                
                # Try to read EXR magic number
                with open(file_path, 'rb') as f:
                    magic = f.read(4)
                    if magic != b'\x76\x2f\x31\x01':  # EXR magic number
                        return False, "Invalid EXR magic number"
                
                # If file is suspiciously small for the expected resolution
                if file_size < 10000:  # Less than ~10KB is suspicious for any real render
                    return False, f"Suspiciously small: {file_size} bytes"
                
                return True, "OK (basic check)"
                
        except Exception as e:
            return False, f"Read error: {str(e)}"
    
    def check_sequence(self, folder, start_frame, end_frame):
        # Check if all frames exist and are valid
        try:
            files = os.listdir(folder)
        except Exception as e:
            return f"ERROR: Cannot read folder!\n{str(e)}"
        
        expected_frames = list(range(start_frame, end_frame + 1))
        found_frames = []
        corrupt_files = []
        
        # Find all .exr files and extract frame numbers
        for f in files:
            if f.endswith('.exr'):
                file_path = os.path.join(folder, f)
                
                # Check if EXR is valid
                is_valid, reason = self.is_valid_exr(file_path)
                if not is_valid:
                    file_size = os.path.getsize(file_path)
                    corrupt_files.append(f"{f} - {reason} ({file_size} bytes)")
                    continue
                
                # IMPROVED: Use regex to extract frame number
                # Pattern: .0001.exr or _0001.exr at the end of filename
                match = re.search(r'[\._](\d{4})\.exr$', f)
                if match:
                    frame_num = int(match.group(1))
                    if start_frame <= frame_num <= end_frame:
                        found_frames.append(frame_num)
        
        found_frames = sorted(set(found_frames))
        missing_frames = [f for f in expected_frames if f not in found_frames]
        
        # Build report
        report = "="*60 + "\n"
        report += "VALIDATION REPORT\n"
        report += "="*60 + "\n\n"
        report += f"Folder: {folder}\n"
        report += f"Expected Frames: {start_frame}-{end_frame} ({len(expected_frames)} frames)\n"
        report += f"Found Valid: {len(found_frames)} frames\n\n"
        
        # Check if passed
        passed = (len(missing_frames) == 0 and len(corrupt_files) == 0)
        
        if passed:
            report += " === STATUS: PASSED === \n"
            report += "All frames rendered successfully!\n"
        else:
            report += " --- STATUS: FAILED --- \n\n"
            
            # Missing frames
            if missing_frames:
                report += f"Missing Frames ({len(missing_frames)}):\n"
                if len(missing_frames) <= 20:
                    report += f"  {missing_frames}\n"
                else:
                    report += f"  {missing_frames[:20]}\n"
                    report += f"  ... and {len(missing_frames)-20} more\n"
                report += "\n"
            
            # Corrupt/Bad files
            if corrupt_files:
                report += f"Corrupt/Invalid Files ({len(corrupt_files)}):\n"
                for cf in corrupt_files[:15]:
                    report += f"  {cf}\n"
                if len(corrupt_files) > 15:
                    report += f"  ... and {len(corrupt_files)-15} more\n"
                report += "\n"
        
        report += "="*60
        
        # Also print to script editor
        print("\n" + report)
        
        return report

# Run
manager = ArnoldRenderManager()
manager.create_ui()
