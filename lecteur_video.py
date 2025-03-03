import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QSlider, QScrollArea, QSizePolicy, QComboBox
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QTime

def resource_path(relative_path):
    """
    Retourne le chemin absolu vers une ressource, compatible avec PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class CustomVideoWidget(QVideoWidget):
    """
    QVideoWidget personnalisé qui gère le double-clic pour le plein écran.
    """
    def mouseDoubleClickEvent(self, event):
        if self.isFullScreen():
            self.setFullScreen(False)
        else:
            self.setFullScreen(True)
        super().mouseDoubleClickEvent(event)

class MainScreen(QWidget):
    """
    Écran principal présentant la liste des vidéos dans un QScrollArea.
    """
    def __init__(self, items, switch_to_video_callback, parent=None):
        super().__init__(parent)
        self.items = items
        self.switch_to_video_callback = switch_to_video_callback
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Liste des vidéos")
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font()
        font.setPointSize(18)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)
        layout.addSpacing(20)
        
        # Zone défilante pour la liste des vidéos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setSpacing(10)
        vbox.setContentsMargins(10, 10, 10, 10)
        
        # Création d'un bouton par vidéo
        for index, (number, title, video_path) in enumerate(self.items):
            btn = QPushButton(f"{number}. {title}")
            btn.setFixedHeight(35)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(lambda checked, idx=index: self.switch_to_video_callback(idx))
            vbox.addWidget(btn)
        vbox.addStretch()
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

class VideoScreen(QWidget):
    """
    Écran de lecture vidéo avec contrôles améliorés :
    - Boutons Précédent, Play/Pause, Suivant
    - Curseur de vitesse appliquant le taux lors du relâchement
    - Contrôle de volume, position et affichage du temps
    - Bouton Recommencer placé à droite de la barre de contrôle
    - Sélecteur de mode de lecture (Boucle, Suivant, Aléatoire)
    """
    def __init__(self, media_player, playlist, parent=None):
        super().__init__(parent)
        self.media_player = media_player
        self.playlist = playlist
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Barre supérieure avec bouton de retour
        top_layout = QHBoxLayout()
        self.back_button = QPushButton("← Retour")
        self.back_button.setFixedWidth(80)
        top_layout.addWidget(self.back_button, alignment=Qt.AlignLeft)
        top_layout.addStretch()
        self.layout.addLayout(top_layout)
        
        # Vidéo agrandie
        self.video_widget = CustomVideoWidget()
        self.video_widget.setMinimumSize(640, 480)
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.video_widget, stretch=1)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Barre de contrôle principale
        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton("Précédent")
        self.prev_button.setFixedSize(80, 30)
        controls_layout.addWidget(self.prev_button)
        self.play_pause_button = QPushButton("Pause")
        self.play_pause_button.setFixedSize(80, 30)
        controls_layout.addWidget(self.play_pause_button)
        self.next_button = QPushButton("Suivant")
        self.next_button.setFixedSize(80, 30)
        controls_layout.addWidget(self.next_button)
        
        # Curseur de position (largeur ajustable)
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        controls_layout.addWidget(self.position_slider)
        
        # Label affichant le temps
        self.time_label = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.time_label)
        
        # Bouton Recommencer à droite
        self.restart_button = QPushButton("Recommencer")
        self.restart_button.setFixedSize(100, 30)
        controls_layout.addWidget(self.restart_button)
        self.layout.addLayout(controls_layout)
        
        # Barre de réglages secondaires (volume, vitesse et mode)
        settings_layout = QHBoxLayout()
        
        # Contrôle du volume
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume:")
        volume_label.setFixedWidth(50)
        volume_layout.addWidget(volume_label)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.media_player.volume())
        self.volume_slider.setFixedWidth(100)
        volume_layout.addWidget(self.volume_slider)
        settings_layout.addLayout(volume_layout)
        
        settings_layout.addSpacing(20)
        
        # Contrôle de la vitesse de lecture
        speed_layout = QHBoxLayout()
        speed_label = QLabel("Vitesse:")
        speed_label.setFixedWidth(50)
        speed_layout.addWidget(speed_label)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(100)
        self.speed_slider.setFixedWidth(100)
        speed_layout.addWidget(self.speed_slider)
        self.speed_value_label = QLabel("1.00x")
        self.speed_value_label.setFixedWidth(40)
        speed_layout.addWidget(self.speed_value_label)
        settings_layout.addLayout(speed_layout)
        
        settings_layout.addSpacing(20)
        
        # Sélecteur de mode de lecture
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode:")
        mode_label.setFixedWidth(40)
        mode_layout.addWidget(mode_label)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Boucle", "Suivant", "Aléatoire"])
        self.mode_combo.setFixedWidth(120)
        mode_layout.addWidget(self.mode_combo)
        settings_layout.addLayout(mode_layout)
        
        settings_layout.addStretch()
        self.layout.addLayout(settings_layout)

    def connect_signals(self):
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.prev_button.clicked.connect(self.play_previous)
        self.next_button.clicked.connect(self.play_next)
        self.restart_button.clicked.connect(self.restart_video)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.volume_slider.valueChanged.connect(self.media_player.setVolume)
        # Mise à jour du label en direct lors du glissement
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        # Application du nouveau taux lors du relâchement du slider
        self.speed_slider.sliderReleased.connect(self.apply_speed)
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.stateChanged.connect(self.update_play_pause_button)
        self.mode_combo.currentIndexChanged.connect(self.change_mode)

    def toggle_play_pause(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def play_previous(self):
        current_index = self.playlist.currentIndex()
        if current_index > 0:
            self.playlist.setCurrentIndex(current_index - 1)
        else:
            self.playlist.setCurrentIndex(self.playlist.mediaCount() - 1)
        self.media_player.play()

    def play_next(self):
        current_index = self.playlist.currentIndex()
        if current_index < self.playlist.mediaCount() - 1:
            self.playlist.setCurrentIndex(current_index + 1)
        else:
            self.playlist.setCurrentIndex(0)
        self.media_player.play()

    def restart_video(self):
        self.media_player.setPosition(0)
        self.media_player.play()

    def update_speed_label(self, value):
        rate = value / 100.0
        self.speed_value_label.setText(f"{rate:.2f}x")

    def apply_speed(self):
        value = self.speed_slider.value()
        rate = value / 100.0
        self.media_player.setPlaybackRate(rate)
        # Forcer un rafraîchissement sans réinitialiser la sortie vidéo
        self.video_widget.repaint()

    def change_mode(self, index):
        """
        Change le mode de lecture en fonction du choix dans le combo.
        Boucle  : CurrentItemInLoop
        Suivant : Sequential
        Aléatoire : Random
        """
        if self.mode_combo.currentText() == "Boucle":
            self.playlist.setPlaybackMode(QMediaPlaylist.CurrentItemInLoop)
        elif self.mode_combo.currentText() == "Suivant":
            self.playlist.setPlaybackMode(QMediaPlaylist.Sequential)
        elif self.mode_combo.currentText() == "Aléatoire":
            self.playlist.setPlaybackMode(QMediaPlaylist.Random)

    def set_position(self, position):
        self.media_player.setPosition(position)

    def update_position(self, position):
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(position)
        self.position_slider.blockSignals(False)
        self.update_time_label(position, self.media_player.duration())

    def update_duration(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_time_label(self.media_player.position(), duration)

    def update_time_label(self, position, duration):
        pos_time = QTime(0, 0, 0).addMSecs(position)
        dur_time = QTime(0, 0, 0).addMSecs(duration)
        format_str = "mm:ss" if duration < 3600 * 1000 else "hh:mm:ss"
        self.time_label.setText(f"{pos_time.toString(format_str)} / {dur_time.toString(format_str)}")

    def update_play_pause_button(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_pause_button.setText("Pause")
        else:
            self.play_pause_button.setText("Play")

class MainWindow(QMainWindow):
    """
    Fenêtre principale gérant les écrans et la lecture vidéo.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lecteur Vidéo Optimisé")
        self.resize(1000, 800)
        self.setup_media()
        self.setup_ui()

    def setup_media(self):
        self.media_player = QMediaPlayer(self)
        self.playlist = QMediaPlaylist(self)
        self.media_player.setPlaylist(self.playlist)

    def setup_ui(self):
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        self.video_items = [
            (1, "Vidéo 1", resource_path(os.path.join("video", "video1.mp4"))),
            (2, "Vidéo 2", resource_path(os.path.join("video", "video2.mp4"))),
            (3, "Vidéo 3", resource_path(os.path.join("video", "video3.mp4"))),
            (4, "Vidéo 4", resource_path(os.path.join("video", "video4.mp4"))),
        ]
        
        self.main_screen = MainScreen(self.video_items, self.show_video)
        self.stacked_widget.addWidget(self.main_screen)
        
        self.video_screen = VideoScreen(self.media_player, self.playlist)
        self.video_screen.back_button.clicked.connect(self.go_back)
        self.stacked_widget.addWidget(self.video_screen)
        
        self.stacked_widget.setCurrentWidget(self.main_screen)

    def show_video(self, selected_index):
        self.playlist.clear()
        for _, _, vp in self.video_items:
            if os.path.exists(vp):
                media = QMediaContent(QUrl.fromLocalFile(vp))
                self.playlist.addMedia(media)
        self.playlist.setCurrentIndex(selected_index)
        # Mode par défaut : lecture suivante
        self.playlist.setPlaybackMode(QMediaPlaylist.Sequential)
        self.media_player.play()
        self.stacked_widget.setCurrentWidget(self.video_screen)

    def go_back(self):
        self.media_player.stop()
        self.stacked_widget.setCurrentWidget(self.main_screen)

def main():
    app = QApplication(sys.argv)
    
    app.setStyleSheet("""
        QWidget {
            background-color: #ecf0f1;
            font-family: Arial;
            font-size: 14px;
        }
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 4px 8px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QLabel {
            color: #2c3e50;
        }
        QSlider::groove:horizontal {
            border: 1px solid #bdc3c7;
            height: 8px;
            background: #bdc3c7;
            margin: 0px;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: #3498db;
            border: 1px solid #2980b9;
            width: 12px;
            margin: -5px 0;
            border-radius: 6px;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
