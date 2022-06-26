import os
import time
import json
import threading

from os.path import join
from random import randint, shuffle

import cv2
import numpy as np

import bluetooth # pybluez - 3.9
from pygame import mixer


class MyPlayer(threading.Thread):

    """
    Clase para la reproduccion de sonidos. Permite la reproduccion de sonidos cuando un marcador se posiciona sobre una de las teclas del 
    juego "Simon", si hay un sonido reproduciendose evita su reproducción. Esta clase hereda de la clase Thread para la creación de hilos y 
    agrega la clase mixer para la reproducción de sonidos.
    """
    num_players = 0
    players = []
    time_sleep = 0.8

    def __init__(self):

        """
        Función de inicializacion de la clase
        """

        threading.Thread.__init__(self)
        self.id_player = MyPlayer.num_players
        
        self.playing = False
        self.mixer = mixer
        self.mixer.init()
        self.mixer.music.set_volume(0.3)

        MyPlayer.num_players += 1
        MyPlayer.players.append(self)

    def play(self,sound_name: str=None) -> None:

        """
        Función para la inicializacion del hilo y posterior reproduccion de sonidos mediante la función run()
        """

        threading.Thread.__init__(self)

        if sound_name != None and type(sound_name) == type(""):
            
            self.sound_name = sound_name
            self.mixer.music.load(self.sound_name)

        if self.is_playing():
            
            return None

        else:

            self.playing = True
            self.start()

    def run(self):

        """
        Función para reproducir sonidos mediante el hilo.
        """

        try:
            
            self.mixer.music.play()

        except:

            pass
            
        time.sleep(0.5)
        self.playing = False
            
    def is_playing(self) -> bool:

        """
        Función que verifica si se esta reproduciendo un sonido
        """

        return self.playing

class InteractivePen(threading.Thread):

    """
    Clase para la realizar la conexión via bluetooth del marcador. La clase hereda de la clase Thread para realizar el proceso de busqueda 
    y conexión en un hilo, de esta manera la interación bluetooth se realiza de manera paralela al proceso permitiendo que la aplicación corra
    de manera fluida. Se agra la clase bluetooth para la conexión
    """

    num_connections = 0
    auto_recognize_device = "RV"
    time_sleep = 0.8

    def __init__(self): # Constructor

        threading.Thread.__init__(self)
        self.id_connection = InteractivePen.num_connections
        self.connected = False
        self.status = False

        InteractivePen.num_connections += 1

    def initialize(self):

        # Iniciamos un nuevo thread
        threading.Thread.__init__(self)
        
        self.status = True

        print("Buscando dispositivos BT...")
        self.nearby_devices = bluetooth.discover_devices()
        nombres = list(map(bluetooth.lookup_name,self.nearby_devices))

        if InteractivePen.auto_recognize_device in nombres:
            print("Encontramos el dispositivo: ",InteractivePen.auto_recognize_device)
            selection = nombres.index(InteractivePen.auto_recognize_device)
            # ya tengo mi dispositivo
            self.bd_addr = self.nearby_devices[selection]

        else:
            
            print("Dispositivos encontrados:")
            for i, device in enumerate(nombres):
                print(i+1,":",device)

            selection = int(input("> ")) - 1
            print("Dispositivo seleccionado:", bluetooth.lookup_name(self.nearby_devices[selection]))
            self.bd_addr = self.nearby_devices[selection]

        self.port = 1

        self.start()

    def run(self):

        """
        Función que se corre dentro del hilo.
        """
        with bluetooth.BluetoothSocket() as self.sock: #bluetooth.RFCOMM
    
            try:
                print("Conectando a:", self.bd_addr)
                self.sock.connect((self.bd_addr, self.port))
                self.connected = True
                print("Dispositivo BT conectado")
            except:
                self.status = False
                self.connected = False
                print("Fallo la conexion BT")

            try:
                while self.status:
                    data = self.sock.recv(1024)
                    if not data:
                        break
                    # print("Recibido: ", data)
                    data = data.decode("utf-8")
                    if data.find("1") >= 0:
                        self.new_data = True
                        self.data = "b" # mayor prioridad es simular "b"
                    elif data.find("2") >= 0:
                        self.new_data = True
                        self.data = "d" # segundo es "d"
                    elif data.find("3") >= 0:
                        self.new_data = True
                        self.data = "c" # tercero es "c"
                    else:
                        self.new_data = False
                        self.data = ""
                    print("BT:",self.data)
            except:
                self.connected = False
                self.status = False
                print("Finalizando BT")

    def is_connected(self):
        return self.connected and self.status

    def disconnect(self):
        self.status = False
        self.sock.close()

def draw_border(img, pt1, pt2, color, thickness, r, d):

    """
    Función para resaltar los bordes sobre los que pasa el marcador.
    """

    x1,y1 = pt1
    x2,y2 = pt2
    # Top left
    cv2.line(img, (x1 + r, y1), (x1 + r + d, y1), color, thickness)
    cv2.line(img, (x1, y1 + r), (x1, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
    # Top right
    cv2.line(img, (x2 - r, y1), (x2 - r - d, y1), color, thickness)
    cv2.line(img, (x2, y1 + r), (x2, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
    # Bottom left
    cv2.line(img, (x1 + r, y2), (x1 + r + d, y2), color, thickness)
    cv2.line(img, (x1, y2 - r), (x1, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)
    # Bottom right
    cv2.line(img, (x2 - r, y2), (x2 - r - d, y2), color, thickness)
    cv2.line(img, (x2, y2 - r), (x2, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)

def add_obj(background, img, mask, x, y):

    '''
    Función para agregar objetos a la pantalla
    '''
    
    bg = background.copy()
    
    h_bg, w_bg = bg.shape[0], bg.shape[1]
    
    h, w = img.shape[0], img.shape[1]
    
    x = x - int(w/2)
    y = y - int(h/2)    
    
    mask_boolean = mask[:,:,0] == 0
    mask_rgb_boolean = np.stack([mask_boolean, mask_boolean, mask_boolean], axis=2)
    
    if x >= 0 and y >= 0:
    
        h_part = h - max(0, y+h-h_bg)
        w_part = w - max(0, x+w-w_bg) 

        bg[y:y+h_part, x:x+w_part, :] = bg[y:y+h_part, x:x+w_part, :] * ~mask_rgb_boolean[0:h_part, 0:w_part, :] + (img * mask_rgb_boolean)[0:h_part, 0:w_part, :]
        
    elif x < 0 and y < 0:
        
        h_part = h + y
        w_part = w + x
        
        bg[0:0+h_part, 0:0+w_part, :] = bg[0:0+h_part, 0:0+w_part, :] * ~mask_rgb_boolean[h-h_part:h, w-w_part:w, :] + (img * mask_rgb_boolean)[h-h_part:h, w-w_part:w, :]
        
    elif x < 0 and y >= 0:
        
        h_part = h - max(0, y+h-h_bg)
        w_part = w + x
        
        bg[y:y+h_part, 0:0+w_part, :] = bg[y:y+h_part, 0:0+w_part, :] * ~mask_rgb_boolean[0:h_part, w-w_part:w, :] + (img * mask_rgb_boolean)[0:h_part, w-w_part:w, :]
        
    elif x >= 0 and y < 0:
        
        h_part = h + y
        w_part = w - max(0, x+w-w_bg)
        
        bg[0:0+h_part, x:x+w_part, :] = bg[0:0+h_part, x:x+w_part, :] * ~mask_rgb_boolean[h-h_part:h, 0:w_part, :] + (img * mask_rgb_boolean)[h-h_part:h, 0:w_part, :]
    
    return bg

class VirtualBoard():
    
    
    _OBJECT_DETECTION_PARAMETERS_FILE = "detection_params.json"
    _OBJECT_DETECTION_PARAMETERS = {"low": {"H": 34, "S": 50, "V": 42}, "high": {"H": 100, "S": 213, "V": 249}}
    OBJECT_MIN_AREA = 800
    
    GUI_color = (10,10,10) # color de la interfaz
    GUI_thickness = 2 # ancho en px de los trazos
    GUI_separation = 10
    GUI_iconsize = 52
    GUI_height = 480 # 720, 480
    GUI_width = 720 # 1080, 720

    # Colores para pintar
    COLOR = {
        "blue":     (255,0,0),
        "red":      (0,0,255),
        "cyan":     (255,113,82),
        "yellow":   (89,222,255),
        "pink":     (128,0,255),
        "green":    (0,255,36),
        "orange":   (29,112,246),
        "white":    (255,255,255)
    }

    # Grosor de línea recuadros superior derecha (grosor del marcador para dibujar)
    THICKNESS = {
        # "xs":1,
        "xs":2,
        "sm":3,
        "md":6,
        "lg":8
    }

    centro_x = 0 # int(VirtualBoard.GUI_width/2)
    centro_y = 0 #int(VirtualBoard.GUI_height/2)

    radio = 0 #min(VirtualBoard.centro_x,VirtualBoard.centro_y)-100
    radio_int = 0 #int(VirtualBoard.radio/2)

    # procesa la posicion del puntero y los eventos de las acciones
    def __init__(self) -> None:
        
        self.t_creation = time.time()
        # Crear la camara
        print(">>> Creating camera object...")
        self.cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, VirtualBoard.GUI_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VirtualBoard.GUI_height)
        VirtualBoard.GUI_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        VirtualBoard.GUI_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Cargando parámetros del reconocimiento
        print(">>> Loading object detection parameters...")
        with open(VirtualBoard._OBJECT_DETECTION_PARAMETERS_FILE,"r") as f:
            rango_detection = json.loads(f.read())

        self.object_filter_low = np.array(list(rango_detection["low"].values()), np.uint8)
        self.object_filter_high = np.array(list(rango_detection["high"].values()), np.uint8)

        #--------------------- Variables para el marcador / lápiz virtual -------------------------
        print(">>> Setting up marker parameters...")
        self.marker_color = VirtualBoard.COLOR["cyan"]  # Color de entrada, y variable que asignará el color del marcador
        self.marker_thickness = VirtualBoard.THICKNESS["sm"] # Grosor que tendrá el marcador
        #------------------------------------------------------------------------------------------

        # Creacion de menus y funcionalidades disponibles de la app
        self.menu_list = []

        self.x1 = None # Posicion previa del marcador en x
        self.y1 = None # Posicion previa del marcador en y
        self.x0 = None # Posicion anterior a la previa del marcador en x
        self.y0 = None # Posicion anterior a la previa del marcador en y
        self.canvas_imAux = None # Lienzo de dibujo
        
        self.t_creation = time.time() - self.t_creation

        self.active_menu, self.active_menu_id = None, None

        self.running = False

        # variables del draw menu
        self.draw_status = None

        # variables del question game
        self.question_status = None
        self.question_answers = None
        self.questions = None

        # variables para el juego de simon
        self.game_options = ["g","r","b","y"]

        self.game_status = None # si estamos jugando o no
        self.game_mostrando = True
        self.game_escuchando = False

        self.game_simon = None # lista con la secuencia a mostrar
        self.game_answer = None # lista con la secuencia que ingresa el usuario
        self.game_mostrando_lista = None # lista auxiliar de mostrando o escuchando
        self.game_escuchando_lista = None # lista auxiliar de mostrando o escuchando
        # crear matrices para dibujar simon


        # Parametros del simon
        VirtualBoard.centro_x = int(VirtualBoard.GUI_width/2)
        VirtualBoard.centro_y = int(VirtualBoard.GUI_height/2)

        VirtualBoard.radio = min(VirtualBoard.centro_x,VirtualBoard.centro_y)-100
        VirtualBoard.radio_int = int(VirtualBoard.radio/2)

        self.Player = MyPlayer()
        try:
            self.BT_Pen = InteractivePen()
            self.BT_Pen.initialize()
        except:
            pass
        
        """
        # Collect events until released
        # with keyboard.Listener(
        #         on_press=on_press,
        #         on_release=on_release) as listener:
        #     listener.join()

        # ...or, in a non-blocking fashion:
        # self.listener = keyboard.Listener(
        #     on_press=self.on_press,
        #     on_release=self.on_release)
        # self.listener.start()
        """

    """
    # Key events
    def on_press(self,key):
        try:
            print('alphanumeric key {0} pressed'.format(
                key.char))
        except AttributeError:
            print('special key {0} pressed'.format(
                key))

    def on_release(self,key):
        print('{0} released'.format(
            key))
        if key == keyboard.Key.esc:
            # Stop listener
            return False
    """

    def cursor_simon(self,cursor):

        radio_cursor = ((cursor[0]-VirtualBoard.centro_x)**2 + (cursor[1]-VirtualBoard.centro_y)**2)**0.5

        if radio_cursor < VirtualBoard.radio_int or radio_cursor > VirtualBoard.radio:
            return ""

        # saber en que cuadrante está y devolver
        if cursor[0] <= VirtualBoard.centro_x and cursor[1] <= VirtualBoard.centro_y:
            return "g"

        elif VirtualBoard.centro_x <= cursor[0] and cursor[1] <= VirtualBoard.centro_y:
            return "r"
            
        elif cursor[0] <= VirtualBoard.centro_x and VirtualBoard.centro_y <= cursor[1]:
            return "y"
            
        elif VirtualBoard.centro_x <= cursor[0] and VirtualBoard.centro_y <= cursor[1]:
            return "b"

        return ""

    def validate_simon(self,respuesta,consigna):
        
        if len(respuesta) != len(consigna):
            return False # si o si está mal
        else:
            for r,c in zip(respuesta,consigna):
                if r == c:
                    continue
                else:
                    return False
            else:
                return True

    def draw_simon(self,fill="",reprod=True):
        """draw_simon
            Esta funcion dibuja en la pantalla el juego del simon y tambien puede pintar algun cuadrante.
            Esto se hace con fill = "g", "r", "b" o "y" según el color a pintar
        Args:
            fill (str, optional): _description_. Defaults to "".
        """

        # creo un frame vacio para dibujar
        self.canvas_imAux = np.zeros(self.frame.shape,dtype=np.uint8)

        # que variables necesito??

        if reprod and fill != "" and not self.Player.is_playing():
            self.Player.play(f"simon/simon_{fill}.wav")

        # que tengo que hacer??
        # Dibujo el Verde en up-left
        cv2.ellipse(self.canvas_imAux,(VirtualBoard.centro_x,VirtualBoard.centro_y),(VirtualBoard.radio,VirtualBoard.radio),0,180,270,VirtualBoard.COLOR['green'],self.marker_thickness if fill != "g" else -1)
        cv2.ellipse(self.canvas_imAux,(VirtualBoard.centro_x,VirtualBoard.centro_y),(VirtualBoard.radio_int,VirtualBoard.radio_int),0,180,270,VirtualBoard.COLOR['green'],self.marker_thickness)
        cv2.line(self.canvas_imAux,(VirtualBoard.centro_x-VirtualBoard.radio,VirtualBoard.centro_y),(VirtualBoard.centro_x-VirtualBoard.radio_int,VirtualBoard.centro_y),VirtualBoard.COLOR['green'],self.marker_thickness)

        cv2.ellipse(self.canvas_imAux,(VirtualBoard.centro_x,VirtualBoard.centro_y),(VirtualBoard.radio,VirtualBoard.radio),0,270,360,VirtualBoard.COLOR['red'],self.marker_thickness if fill != "r" else -1)
        cv2.ellipse(self.canvas_imAux,(VirtualBoard.centro_x,VirtualBoard.centro_y),(VirtualBoard.radio_int,VirtualBoard.radio_int),0,270,360,VirtualBoard.COLOR['red'],self.marker_thickness)
        cv2.line(self.canvas_imAux,(VirtualBoard.centro_x,VirtualBoard.centro_y-VirtualBoard.radio),(VirtualBoard.centro_x,VirtualBoard.centro_y-VirtualBoard.radio_int),VirtualBoard.COLOR['red'],self.marker_thickness)

        cv2.ellipse(self.canvas_imAux,(VirtualBoard.centro_x,VirtualBoard.centro_y),(VirtualBoard.radio,VirtualBoard.radio),0,0,90,VirtualBoard.COLOR['cyan'],self.marker_thickness if fill != "b" else -1)
        cv2.ellipse(self.canvas_imAux,(VirtualBoard.centro_x,VirtualBoard.centro_y),(VirtualBoard.radio_int,VirtualBoard.radio_int),0,0,90,VirtualBoard.COLOR['cyan'],self.marker_thickness)
        cv2.line(self.canvas_imAux,(VirtualBoard.centro_x+VirtualBoard.radio,VirtualBoard.centro_y),(VirtualBoard.centro_x+VirtualBoard.radio_int,VirtualBoard.centro_y),VirtualBoard.COLOR['cyan'],self.marker_thickness)

        cv2.ellipse(self.canvas_imAux,(VirtualBoard.centro_x,VirtualBoard.centro_y),(VirtualBoard.radio,VirtualBoard.radio),0,90,180,VirtualBoard.COLOR['yellow'],self.marker_thickness if fill != "y" else -1)
        cv2.ellipse(self.canvas_imAux,(VirtualBoard.centro_x,VirtualBoard.centro_y),(VirtualBoard.radio_int,VirtualBoard.radio_int),0,90,180,VirtualBoard.COLOR['yellow'],self.marker_thickness)
        cv2.line(self.canvas_imAux,(VirtualBoard.centro_x,VirtualBoard.centro_y+VirtualBoard.radio),(VirtualBoard.centro_x,VirtualBoard.centro_y+VirtualBoard.radio_int),VirtualBoard.COLOR['yellow'],self.marker_thickness)

        # elimino el centro
        cv2.circle(self.canvas_imAux,(VirtualBoard.centro_x,VirtualBoard.centro_y),VirtualBoard.radio_int-self.marker_thickness,(0,0,0),-1) # borramos lo pintado que haya al medio


        # que tengo que devolver o hacer para finalizar??

    def draw_camera(self):
        pass

    def draw_gui(self):
        
        self.t_drawing_gui = time.time()
        for menu in self.menu_list:
            # cv2.rectangle(self.frame,
            # (
            #     menu["x"],
            #     menu["y"]
            # ),
            # (
            #     menu["x"]+menu["size"],
            #     menu["y"]+menu["size"]
            # ),
            # menu["color"],
            # VirtualBoard.THICKNESS["medium"])

            src = menu["icon"]
            y1 = menu["y"]
            y2 = menu["y"]+menu["size"]
            x1 = menu["x"]
            x2 = menu["x"]+menu["size"]

            self.frame[y1:y2, x1:x2] = self.frame[y1:y2, x1:x2] * (1 - src[:, :, 3:] / 255) + src[:, :, :3] * (src[:, :, 3:] / 255)

        
        self.t_drawing_gui = time.time() - self.t_drawing_gui
        return False
        #------------------------ Sección Superior ------------------------------------------
        # Cuadrados dibujados en la parte superior izquierda (representan el color a dibujar)
        cv2.rectangle(self.frame,(0,0),(50,50),VirtualBoard.COLOR["yellow"],VirtualBoard.THICKNESS["normal"])
        cv2.rectangle(self.frame,(50,0),(100,50),VirtualBoard.COLOR["pink"],VirtualBoard.THICKNESS["normal"])
        cv2.rectangle(self.frame,(100,0),(150,50),VirtualBoard.COLOR["green"],VirtualBoard.THICKNESS["normal"])
        cv2.rectangle(self.frame,(150,0),(200,50),VirtualBoard.COLOR["cyan"],VirtualBoard.THICKNESS["normal"])

        # Rectángulo superior central, que nos ayudará a limpiar la pantalla
        cv2.rectangle(self.frame,(300,0),(400,50),colorLimpiarPantalla,1)
        cv2.putText(self.frame,'Limpiar',(320,20),6,0.6,colorLimpiarPantalla,1,cv2.LINE_AA)
        cv2.putText(self.frame,'pantalla',(320,40),6,0.6,colorLimpiarPantalla,1,cv2.LINE_AA)

        # Cuadrados dibujados en la parte superior derecha (grosor del marcador para dibujar)
        cv2.rectangle(self.frame,(490,0),(540,50),(0,0,0),grosorPeque)
        cv2.circle(self.frame,(515,25),3,(0,0,0),-1)
        cv2.rectangle(self.frame,(540,0),(590,50),(0,0,0),grosorMedio)
        cv2.circle(self.frame,(565,25),7,(0,0,0),-1)
        cv2.rectangle(self.frame,(590,0),(640,50),(0,0,0),grosorGrande)
        cv2.circle(self.frame,(615,25),11,(0,0,0),-1)
        #-----------------------------------------------------------------------------------
        
    def object_detection(self):
        
        self.t_object_detection = time.time()
        # Detección del color celeste
        self.maskCeleste = cv2.inRange(self.frameHSV, self.object_filter_low, self.object_filter_high)
        # cv2.imshow('rangeColors', self.maskCeleste)
        self.maskCeleste = cv2.erode(self.maskCeleste,None,iterations = 1)
        self.maskCeleste = cv2.dilate(self.maskCeleste,None,iterations = 2)
        self.maskCeleste = cv2.medianBlur(self.maskCeleste, 13)
        cnts,_ = cv2.findContours(self.maskCeleste, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:1]

        for c in cnts:
            area = cv2.contourArea(c)
            if area > 800:
                x,y2,w,h = cv2.boundingRect(c)
                x2 = x + w//2

                # Corner detection
                # img = cv2.imread('edges.png')
                # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # gray = np.float32(gray)
                # dst = cv2.cornerHarris(gray,5,3,0.04)
                # ret, dst = cv2.threshold(dst,0.1*dst.max(),255,0)
                # dst = np.uint8(dst)
                # ret, labels, stats, centroids = cv2.connectedComponentsWithStats(dst)
                # criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.001)
                # corners = cv2.cornerSubPix(gray,np.float32(centroids),(5,5),(-1,-1),criteria)
                # for i in range(1, len(corners)):
                # 	print(corners[i])
                # img[dst>0.1*dst.max()]=[0,0,255]
                
                cv2.circle(self.frame,(x2,y2),self.marker_thickness,self.marker_color,3)
                self.x1 = x2
                self.y1 = y2
            else:
                self.x1, self.y1 = None, None

        # para devolver --> cursor_detected, cursor_position, cursor_key
        if self.x1 == None and self.y1 == None:
            cursor_detected = False
        else:
            cursor_detected = True
        
        cursor_position = (self.x1,self.y1)

        # if i'm drawing dont do that
        # print("Acion menu", self.active_menu)

        try:
            if self.BT_Pen.is_connected() and self.BT_Pen.new_data:
                cursor_key = ord(self.BT_Pen.data)
                self.BT_Pen.new_data = False
            else:
                cursor_key = cv2.waitKey(1)
        except:
            cursor_key = cv2.waitKey(1)

        # self.t_object_detection = time.time() - self.t_object_detection

        return cursor_detected, cursor_position, cursor_key

    def menu_over(self,cursor_position):
        """
        Recibo la posicion del cursor y la tecla y si está dentro de un menu ejecuto las acciones correspondientes.
        Devuelvo true o false si estoy en menu.
        Dibujo el menu segun corresponda, marcar si estoy encima de algo
        """
        # cursor_position --> (x,y)
        for it,menu in enumerate(self.menu_list):
            cX = cursor_position[0]
            cY = cursor_position[1]
            mX = menu['x']
            mY = menu['y']
            mS = menu['size']

            # si la posicion del cursor está dentro de un menu, pintarlo
            if  (mX <= cX and cX <= mX+mS) and (mY <= cY and cY <= mY+mS):
                
                cv2.rectangle(self.frame,(mX,mY),(mX+mS,mY+mS),self.marker_color,self.marker_thickness)
                
                image = cv2.putText(
                    self.frame, menu["name"],
                    (VirtualBoard.GUI_separation,VirtualBoard.GUI_height-VirtualBoard.GUI_separation),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    self.marker_color,
                    self.marker_thickness,
                    cv2.LINE_AA
                )
                
                return True,menu["name"],it

        else:
            return False,None,None
    
    def menu_action(self,menu, id_menu, cursor_position, cursor_key):
        
        # si entro en un menu lo activo o muestro otras opciones
        if menu == "clean":
            self.canvas_imAux = np.zeros(self.frame.shape,dtype=np.uint8)

        elif menu == "exit":
            self.running = False

        elif menu == "color":
            # desplegar colores, elegir uno y esperar un enter o una tecla
            for i,color in enumerate(VirtualBoard.COLOR.keys()):
                menu_color = self.menu_list[id_menu]
                # print(color)
                x = menu_color['x']
                y = menu_color['y']
                size = menu_color['size']
                sep = VirtualBoard.GUI_separation
                # self.menu_list[]
                X0_option = x+((i+1)*(size+sep))
                Y0_option = y
                X1_option = x+((i+1)*(size+sep))+size
                Y1_option = y+size
                mX = cursor_position[0]
                mY = cursor_position[1]
                try:
                    if (X0_option <= mX and mX <= X1_option) and (Y0_option <= mY and mY <= Y1_option):
                        # dibujo rectangulo relleno y cambio variables
                        cv2.rectangle(self.frame,(X0_option,Y0_option),(X1_option,Y1_option),VirtualBoard.COLOR[color],-1)
                        self.marker_color = VirtualBoard.COLOR[color]

                    else:
                        cv2.rectangle(self.frame,(X0_option,Y0_option),(X1_option,Y1_option),VirtualBoard.COLOR[color],self.marker_thickness)
                except:
                    # print("No mouse position detected")
                    break
            # tomo la posicion

        elif menu == "thickness":
            # desplegar los grosores
            for i,grosor in enumerate(VirtualBoard.THICKNESS.keys()):
                menu_grosor = self.menu_list[id_menu]
                # print(color)
                x = menu_grosor['x']
                y = menu_grosor['y']
                size = menu_grosor['size']
                sep = VirtualBoard.GUI_separation
                # self.menu_list[]
                X0_option = x+((i+1)*(size+sep))
                Y0_option = y
                X1_option = x+((i+1)*(size+sep))+size
                Y1_option = y+size
                mX = cursor_position[0]
                mY = cursor_position[1]
                try:
                    if (X0_option <= mX and mX <= X1_option) and (Y0_option <= mY and mY <= Y1_option):
                        # dibujo rectangulo relleno y cambio variables
                        cv2.rectangle(self.frame,(X0_option,Y0_option),(X1_option,Y1_option),self.marker_color,-1)
                        self.marker_thickness = VirtualBoard.THICKNESS[grosor]

                    else:
                        cv2.rectangle(self.frame,(X0_option,Y0_option),(X1_option,Y1_option),self.marker_color,VirtualBoard.THICKNESS[grosor])
                except:
                    # print("No mouse position detected")
                    break

        # elif menu == "shape":
        #     # desplegar las formas esto es opcional
        #     pass

        elif menu == "questions":

            self.canvas_imAux = np.zeros(self.frame.shape,dtype=np.uint8)
            # trabajamos con 3 variables
            # question_status -> Boolean
            # question_list -> List[Dict]
            # question_answers -> List[Bool]
            
            if self.question_status == None: # Empezar juego desde 0

                self.question_status = True
                self.question_list = []
                self.question_answers = [] # aca se guardan las respuestas

                # Leo las preguntas y creo un objeto
                with open('questions/questions.json',encoding="utf_8") as f:
                    self.question_object = json.load(f)

                # Agarro el formato de la pregunta
                # Itero la lista de animales
                # Y genero la pregunta, la imagen y las respuestas aleatorias (cant opciones)
                # Y poner cual es la correcta y cual no
                pregunta = self.question_object["animales"]["question"]
                original_questions = self.question_object["animales"]["lista"].copy()
                ruta_imagenes = "questions/animals"

                # creo lista con numeros aleatorios de preguntas para mostrar
                random_questions = [x for x in range(len(original_questions))]
                shuffle(random_questions)

                for i,elem in enumerate(random_questions):
                    # voy al json y busco el elemento elem de la lista de animales
                    animal_eng = original_questions[elem][0].title()
                    animal_esp = original_questions[elem][1].upper()
                    size = 144
                    # de la mitad de la pantalla a la izq el ancho de la imagen
                    x = int((VirtualBoard.GUI_width-size)/2)
                    y = int((VirtualBoard.GUI_height-size)/2)

                    #generar ids de las otras opciones random

                    self.question_list.append({
                        "id":elem,
                        "image":{
                            "logo":cv2.imread(join(ruta_imagenes,animal_eng.lower()+".png"), cv2.IMREAD_UNCHANGED),
                            "x":x,
                            "y":y-25,
                            "size":size
                        },
                        "text":{
                            "contenido":pregunta.replace("@animal",animal_esp),
                            "x":x,
                            "y":y+size+15,
                            "size":1
                        },
                        "options":[
                            {
                                "name":animal_eng,
                                "is_correct":True
                            }
                        ]
                    })
                    
                    # generar 3 - 1 elementos o respuestas random distintas a las que tengo
                    numbs = []
                    while len(self.question_list[-1]['options'])<self.question_object["animales"]["max_options"]:
                        j_o = randint(0,len(random_questions)-1)
                        if j_o == elem or j_o in numbs:
                            continue
                        else:
                            numbs.append(j_o)
                            self.question_list[-1]['options'].append({
                                "name":original_questions[j_o][0].title(),
                                "is_correct":False
                            })
                    
                    shuffle(self.question_list[-1]['options'])
            
            else: # seguir juego o finalizar
                
                # si la opcion ya es la ultima y esta respondida mostrar resultado sino seguir
                if self.question_status: # True -> estamos jugando
                    
                    if len(self.question_answers)<len(self.question_list): # faltan opciones
                        
                        # DIBUJAR opcion len(answer)
                        i_q = len(self.question_answers)

                        src = self.question_list[i_q]['image']['logo']
                        x1 = self.question_list[i_q]['image']['x']
                        y1 = self.question_list[i_q]['image']['y']
                        x2 = x1 + self.question_list[i_q]['image']['size']
                        y2 = y1 + self.question_list[i_q]['image']['size']
                        fff = self.frame[y1:y2, x1:x2]

                        xt = self.question_list[i_q]["text"]['x']
                        yt = self.question_list[i_q]["text"]['y']

                        # porque carajos hay error en los rangos!
                        self.frame[y1:y2, x1:x2] = self.frame[y1:y2, x1:x2] * (1 - src[:, :, 3:] / 255) + src[:, :, :3] * (src[:, :, 3:] / 255)
                        preg = self.question_list[i_q]['text']['contenido']
                        txt_size = int(self.question_list[i_q]['text']['size'])
                        cv2.putText(
                            self.frame, preg,
                            (int(xt-6.5*txt_size*len(preg)),int(yt)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            txt_size,
                            self.marker_color,
                            self.marker_thickness,
                            cv2.LINE_AA
                        )

                        # print(self.question_list[i_q]["options"])
                        # [{'name': 'Bird', 'is_correct': False}, {'name': 'Snake', 'is_correct': False}, {'name': 'Bat', 'is_correct': True}]
                        size_rect = 6*30
                        h_rect = 60
                        x_m = int(VirtualBoard.GUI_width/2)
                        y_m = int(VirtualBoard.GUI_height-h_rect-VirtualBoard.GUI_separation)

                        for i,opt in enumerate(self.question_list[i_q]["options"]):

                            x1_rect = x_m+((i-1)*(size_rect+VirtualBoard.GUI_separation))-int(size_rect/2)
                            y1_rect = y_m-h_rect
                            x2_rect = x_m+((i-1)*(size_rect+VirtualBoard.GUI_separation))-int(size_rect/2)+size_rect
                            y2_rect = y_m

                            # si el cursor esta este rectangulo entonces contarla como correcta y mostrar solo esa opcion
                            if x1_rect <= cursor_position[0] and cursor_position[0] <= x2_rect and y1_rect <= cursor_position[1] and cursor_position[1] <= y2_rect:
                                # ver si es correcta, mostrar algo y break
                                if cursor_key == ord("d"):
                                    if opt['is_correct']:
                                        self.question_answers.append(True)
                                    else:
                                        self.question_answers.append(False)
                                    break
                            
                                cv2.rectangle(
                                    self.frame,
                                    (x_m+((i-1)*(size_rect+VirtualBoard.GUI_separation))-int(size_rect/2),y_m-h_rect),
                                    (x_m+((i-1)*(size_rect+VirtualBoard.GUI_separation))-int(size_rect/2)+size_rect,y_m),
                                    self.marker_color,
                                    -1
                                )
                                pos_x_txt = x_m+((i-1)*(size_rect+VirtualBoard.GUI_separation))

                                cv2.putText(
                                    self.frame, opt['name'],
                                    (int(pos_x_txt-6.7*txt_size*len(opt['name'])),int(y_m-20)),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    txt_size,
                                    VirtualBoard.COLOR['white'],
                                    self.marker_thickness,
                                    cv2.LINE_AA
                                )
                            else:
                                cv2.rectangle(
                                    self.frame,
                                    (x_m+((i-1)*(size_rect+VirtualBoard.GUI_separation))-int(size_rect/2),y_m-h_rect),
                                    (x_m+((i-1)*(size_rect+VirtualBoard.GUI_separation))-int(size_rect/2)+size_rect,y_m),
                                    self.marker_color,
                                    self.marker_thickness
                                )
                                pos_x_txt = x_m+((i-1)*(size_rect+VirtualBoard.GUI_separation))

                                cv2.putText(
                                    self.frame, opt['name'],
                                    (int(pos_x_txt-6.7*txt_size*len(opt['name'])),int(y_m-20)),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    txt_size,
                                    self.marker_color,
                                    self.marker_thickness,
                                    cv2.LINE_AA
                                )


                        # mostrar avances
                        texto = f"Puntaje: {len([x for x in self.question_answers if x])}/{len(self.question_list)}"
                        cv2.putText(
                            self.frame, texto,
                            (VirtualBoard.GUI_separation,VirtualBoard.GUI_height-VirtualBoard.GUI_separation),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            txt_size,
                            self.marker_color,
                            self.marker_thickness,
                            cv2.LINE_AA
                        )

                        
                    else: # llegue al final, terminar juego
                        text1 = "Fin del Juego"
                        text2 = f"Aciertos: {len([x for x in self.question_answers if x])} | Fallos: {len([x for x in self.question_answers if not x])}"
                        xt = int(VirtualBoard.GUI_width/2)
                        yt = int(VirtualBoard.GUI_height/2+15)
                        cv2.putText(
                            self.frame, text1,
                            (int(xt-6.5*len(text1)),int(yt)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            self.marker_color,
                            self.marker_thickness,
                            cv2.LINE_AA
                        )
                        cv2.putText(
                            self.frame, text2,
                            (int(xt-6.5*len(text2)),int(yt)+40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            self.marker_color,
                            self.marker_thickness,
                            cv2.LINE_AA
                        )

                else: # False -> finalizo el juego
                    pass

                # el seguir es para ver si el mouse esta sobre una de las opciones y esta es correcta o no.

            # itero una lista de preguntas, y muestro sus posibles respuestas
            # self.question_status = True
            # self.question_answers = None

            # si acierta sumo punto y avanzo sino paso esa pregunta al final y sigo preguntando.
            pass
        
        elif menu == "draw":
            pass
            # dibujo sobre un lienzo, al terminar el dibujo paso el lienzo a reconocimiento
            # es linea, cuadrado, circulo o triangulo?? obtener limites, bordes, areas y demas
            # inserto en otro lienzo el dibujo mejorado y vuelvo a esperar otro dibujo
            pass
        
        elif menu == "game":

            self.canvas_imAux = np.zeros(self.frame.shape,dtype=np.uint8)
            
            # Estados del juego (jugando o no, mostrando secuencia, escuchando secuencia)
            # jugamos al simon
            # una lista con la secuencia mostrada
            # una con la secuencia que voy introduciendo
            # almacenar puntos
            # dibujar interfaz, sonidos

            # Referencia de atributos
            # self.game_status # si estamos jugando o no
            # self.game_answer # lista con la secuencia que ingresa el usuario
            # self.game_simon # lista con la secuencia a mostrar

            if self.game_status == None: # empezar juego desde cero

                print("Empezando juego desde cero")
                self.game_status = True

                # armar el juego para empezar
                self.game_mostrando = True
                self.game_escuchando = False
                self.game_mostrando_lista = []
                self.game_escuchando_lista = []
                self.game_simon = []
                self.game_answer = []

                # for _ in range(1):
                #     aleat = randint(0,len(self.game_options)-1)
                #     self.game_simon.append(self.game_options[aleat])

            else:

                if self.game_status: # estamos jugando
                    
                    # print("Jugando")
                    
                    if self.game_mostrando and not self.game_escuchando:
                        # print("Mostramos la secuencia")

                        if self.Player.is_playing():
                            # mostrar el ultimo
                            try:
                                self.draw_simon(self.game_mostrando_lista[-1])
                            except:
                                self.draw_simon()

                        else:
                        
                            if len(self.game_mostrando_lista) < len(self.game_simon): # tengo mas elementos por mostrar
                                
                                # print("mostrar un elemento mas de la secuencia si el otro ya termino")
                                elem = self.game_simon[len(self.game_mostrando_lista)]
                                self.draw_simon(elem)
                                self.game_mostrando_lista.append(elem)

                            else: # ya mostre todos los elementos
                                self.game_mostrando = False
                                self.game_escuchando = True
                                self.game_escuchando_lista = []
                                self.game_answer = []
                                # print("Terminamos de mostrar iniciamos escucha si ya termino el ultimo")


                    # else: # en que caso estoy mostrando y escuchando?
                    #     # no deberia pasar
                    #     print("Should not happen")

                    if self.game_escuchando and not self.game_mostrando:
                        # print("Escuchando secuencia")
                        # print(self.game_escuchando_lista)
                        # print(self.game_simon)

                        if len(self.game_escuchando_lista) < len(self.game_simon): # tengo que seguir escuchando opciones
                            
                            # print(self.Player.is_playing())
                            if not self.Player.is_playing():
                                # mostrar el ultimo
                                # print("Tengo que seguir escuchando mas steps si ya terminó el anterior")
                                opc = self.cursor_simon(cursor_position)
                                # print("cursor over:",opc)
                                if cursor_key == ord('d'):
                                    self.draw_simon(opc)
                                    self.game_escuchando_lista.append(opc)
                                    valid = self.validate_simon(self.game_escuchando_lista,self.game_simon[:len(self.game_escuchando_lista):])
                                    if valid:
                                        pass # puedo continuar
                                    else:
                                        # print("sino finalizar el juego y mostrar el mensaje")
                                        self.canvas_imAux = np.zeros(self.frame.shape,dtype=np.uint8)
                                        self.game_status = False
                                else:
                                    self.draw_simon(opc,False)

                            else:
                                try:
                                    self.draw_simon(self.game_escuchando_lista[-1])
                                except:
                                    self.draw_simon()

                        else: # ya no hay mas opciones para escuchar
                            
                            # print("Ya escuche todo")
                            self.game_escuchando = False
                            self.game_mostrando = False

                            # print("Validar que sea correcto lo que ingrese")
                            rpta_valida = self.validate_simon(self.game_escuchando_lista,self.game_simon)

                            if rpta_valida:
                                # print("si es correcto agregar steps y pasar a mostrando")
                                self.game_mostrando = True
                                self.game_mostrando_lista = []

                                # for _ in range(3):
                                aleat = self.game_options[randint(0,len(self.game_options)-1)]
                                # ver que no se repita mas de dos veces
                                if len(self.game_simon)>0:
                                    while aleat == self.game_simon[-1] :
                                        aleat = self.game_options[randint(0,len(self.game_options)-1)]
                                self.game_simon.append(aleat)

                            else:
                                # print("sino finalizar el juego y mostrar el mensaje")
                                self.canvas_imAux = np.zeros(self.frame.shape,dtype=np.uint8)
                                self.game_status = False

                    # else: # en que caso estoy escuchando y mostrando?

                    #     # no deberia pasar
                    #     print("Should not happen")

                else: #  termino el juego
                    text1 = "Fin del Juego"
                    xt = int(VirtualBoard.GUI_width/2)
                    yt = int(VirtualBoard.GUI_height/2+15)
                    cv2.putText(
                        self.frame, text1,
                        (int(xt-6.5*len(text1)),int(yt)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        self.marker_color,
                        self.marker_thickness,
                        cv2.LINE_AA
                    )
                    # print("Fin del juego")    
            
        elif menu == "freedraw":


            if cursor_key == ord("d"):
                self.draw_status = True

            elif cursor_key == ord("c"):
                self.draw_status = False

            elif cursor_key != -1:
                self.draw_status = None

            if self.x0 != None and self.y0 != None and self.x1 != None and self.y1 != None and self.draw_status != None:
                    
                if self.draw_status:
                    mX = cursor_position[0]
                    mY = cursor_position[1]
                    self.canvas_imAux = cv2.line(self.canvas_imAux,(self.x0,self.y0),(mX,mY),self.marker_color,self.marker_thickness)
                
                else:
                    mX = cursor_position[0]
                    mY = cursor_position[1]
                    self.canvas_imAux = cv2.line(self.canvas_imAux,(self.x0,self.y0),(mX,mY),(0,0,0),self.marker_thickness*20)
        
        elif self.active_menu == None:
            self.draw_status = None
            # self.question_status = None

            # RESET GAME OPTIONS
            # self.game_status = None # si estamos jugando o no
    
    # hacer, deshacer, volver atras

    def menu_creation(self):
        
        self.t_menu_creation = time.time()

        # Creacion de menus y funcionalidades disponibles de la app
        self.menu_list = []

        # Cargo el archivo gui
        with open("gui.json") as f:
            menus_dicc = json.loads(f.read())

        it = 0
        for key,value in menus_dicc.items():
            print(key,value)
            
            menu_aux = value

            if key == "NW":
                try:
                    if(not os.path.exists(menu_aux["icon_path"])):
                        print('NOT EXIST! = ' + menu_aux["icon_path"])
                        continue
                except:
                    continue
                menu_aux.update({
                    "id":len(self.menu_list),
                    "x":VirtualBoard.GUI_separation,
                    "y":VirtualBoard.GUI_separation,
                    "size":VirtualBoard.GUI_iconsize,
                    "color":VirtualBoard.COLOR["cyan"],
                    "icon":cv2.imread(menu_aux["icon_path"], cv2.IMREAD_UNCHANGED)
                })
                self.menu_list.append(menu_aux)

            elif key == "NE":
                try:
                    if(not os.path.exists(menu_aux["icon_path"])):
                        print('NOT EXIST! = ' + menu_aux["icon_path"])
                        continue
                except:
                    continue
                menu_aux.update({
                    "id":len(self.menu_list),
                    "x":VirtualBoard.GUI_width - VirtualBoard.GUI_iconsize - VirtualBoard.GUI_separation,
                    "y":VirtualBoard.GUI_separation,
                    "size":VirtualBoard.GUI_iconsize,
                    "color":VirtualBoard.COLOR["cyan"],
                    "icon":cv2.imread(menu_aux["icon_path"], cv2.IMREAD_UNCHANGED)
                })
                self.menu_list.append(menu_aux)

            elif key == "SE":
                try:
                    if(not os.path.exists(menu_aux["icon_path"])):
                        print('NOT EXIST! = ' + menu_aux["icon_path"])
                        continue
                except:
                    continue
                menu_aux.update({
                    "id":len(self.menu_list),
                    "x":VirtualBoard.GUI_width - VirtualBoard.GUI_iconsize - VirtualBoard.GUI_separation,
                    "y":VirtualBoard.GUI_height - VirtualBoard.GUI_iconsize - VirtualBoard.GUI_separation,
                    "size":VirtualBoard.GUI_iconsize,
                    "color":VirtualBoard.COLOR["cyan"],
                    "icon":cv2.imread(menu_aux["icon_path"], cv2.IMREAD_UNCHANGED)
                })
                self.menu_list.append(menu_aux)

            elif key == "N":

                # desde que x empiezo
                x_0 = int(VirtualBoard.GUI_width / 2)
                cant_items = len(value)
                x_0 -= int(( cant_items*VirtualBoard.GUI_iconsize + (cant_items+1)*VirtualBoard.GUI_separation )/2)
                
                for i,internal_menu in enumerate(value):
                    menu_aux = internal_menu
                    try:
                        if(not os.path.exists(menu_aux["icon_path"])):
                            print('NOT EXIST! = ' + menu_aux["icon_path"])
                            continue
                    except:
                        continue
                    
                    menu_aux.update({
                        "id":len(self.menu_list),
                        "x":x_0+(i*(VirtualBoard.GUI_iconsize+VirtualBoard.GUI_separation)),
                        "y":VirtualBoard.GUI_separation,
                        "size":VirtualBoard.GUI_iconsize,
                        "color":VirtualBoard.COLOR["cyan"],
                        "icon":cv2.imread(menu_aux["icon_path"], cv2.IMREAD_UNCHANGED)
                    })
                    self.menu_list.append(menu_aux)

            elif key == "W":

                # desde que y empiezo
                y_0 = int(VirtualBoard.GUI_height / 2)
                cant_items = len(value)
                y_0 -= int(( cant_items*VirtualBoard.GUI_iconsize + (cant_items+1)*VirtualBoard.GUI_separation )/2)
                
                for i,internal_menu in enumerate(value):
                    menu_aux = internal_menu
                    try:
                        if(not os.path.exists(menu_aux["icon_path"])):
                            print('NOT EXIST! = ' + menu_aux["icon_path"])
                            continue
                    except:
                        continue
                    
                    menu_aux.update({
                        "id":len(self.menu_list),
                        "x":VirtualBoard.GUI_separation,
                        "y":y_0+(i*(VirtualBoard.GUI_iconsize+VirtualBoard.GUI_separation)),
                        "size":VirtualBoard.GUI_iconsize,
                        "color":VirtualBoard.COLOR["cyan"],
                        "icon":cv2.imread(menu_aux["icon_path"], cv2.IMREAD_UNCHANGED)
                    })
                    self.menu_list.append(menu_aux)
            
            elif key == "E":
                pass

            else:
                print("Posicion erronea")
                continue
            it += 1
        
        
        self.t_menu_creation = time.time() - self.t_menu_creation

# =======================================

    def cursor_action(self):
        pass

    def configure_marker(self):
        pass

    def show_message(self):
        pass

# =======================================

    def end_board(self):
        
        self.BT_Pen.disconnect()
        self.running = False
        self.cap.release()
        cv2.destroyAllWindows()

    def start_board(self):
        self.running = True
        while self.running:

            # if not self.BT_Pen.status:
            #     self.BT_Pen.initialize()

            # Obtenemos la imagen de la cámara
            ret,self.frame = self.cap.read()
            if ret==False: break

            # Espejamos la camara y convertimos a HSV
            self.frame = cv2.flip(self.frame,1)
            self.frameHSV = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
            if self.canvas_imAux is None: self.canvas_imAux = np.zeros(self.frame.shape,dtype=np.uint8) # Si el lienzo es nulo lo hacemos todos ceros

            # Aplicamos mascara para obtener el cursor
            cursor_detected, cursor_position, cursor_key = self.object_detection()

            # Ver si la tecla era de salida
            if cursor_key == ord("q") or cursor_key == 27: # Esc
                
                self.BT_Pen.disconnect()
                self.running = False
                break

            elif cursor_key == ord("b"):
                self.active_menu = None
                self.active_menu_id = None

            self.draw_gui()
            
            if cursor_detected:
                # El cursor está en una posicion de menú
                over_menu, menu_name, menu_id  = self.menu_over(cursor_position)
                if over_menu:

                    # Si estoy sobre algún menu se pierde la info de todos y vuelvo a empezar
                    
                    # Reiniciando questions
                    self.question_status = None
                    self.question_list = None
                    self.question_answers = None

                    self.game_status = None
                    # self.game_simon = None
                    # self.game_answer = None
                    self.prev_menu = self.active_menu 
                    self.active_menu = menu_name
                    self.active_menu_id = menu_id

                    if self.prev_menu == "game" and self.active_menu == "freedraw":
                         self.canvas_imAux = np.zeros(self.frame.shape,dtype=np.uint8)

                # # Si no estoy sobre un menu entonces tengo que dibujar o algo
                # self.cursor_action(cursor_position) # las acciones dependep del menu
            
            # self.menu_action(self.active_menu, self.active_menu_id, cursor_position,cursor_key)
            try:
                self.menu_action(self.active_menu, self.active_menu_id, cursor_position,cursor_key)
            except:
                # esto sacarlo despues
                # self.menu_action(self.active_menu, self.active_menu_id, cursor_position,cursor_key)
                pass

            # Actualizamos variables para prox iteracion
            self.x0, self.y0 = cursor_position
            
            # unimos todas las capas e imagenes
            imAuxGray = cv2.cvtColor(self.canvas_imAux,cv2.COLOR_BGR2GRAY)
            _, th = cv2.threshold(imAuxGray,10,255,cv2.THRESH_BINARY)
            thInv = cv2.bitwise_not(th)
            self.frame = cv2.bitwise_and(self.frame,self.frame,mask=thInv)
            self.frame = cv2.add(self.frame,self.canvas_imAux)
            
            # mostramos las distintas capas
            cv2.imshow('maskCeleste', self.maskCeleste)
            # cv2.imshow('imAux',self.canvas_imAux)
            cv2.imshow('frame', self.frame)
        else:
            self.BT_Pen.disconnect()
            

if __name__ == "__main__":

    # Creamos la pizarra virtual
    vboard = VirtualBoard()

    # Creamos los menus que tiene el programa
    vboard.menu_creation()

    # Iniciamos la pizarra
    vboard.start_board()

    # Fin del programa
    vboard.end_board()

    vboard.BT_Pen.disconnect()