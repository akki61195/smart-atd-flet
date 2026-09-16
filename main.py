from datetime import datetime, timezone, timedelta
import io
import math
import flet as ft
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import requests

# Google Sheet URLs
OLD_SHEET_ID = "1vfioGSmpC7a5S8SMUpCk9xn-mtttvcTecLEQ1Sd6XkU"
OLD_SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{OLD_SHEET_ID}/export?format=csv"
)

NEW_SHEET_ID = "1VYubXUbniIrCNZlybPQD8lC71SS2wBYlR-kF_EtD5IY"
NEW_SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{NEW_SHEET_ID}/export?format=csv"
)

ist_offset = timezone(timedelta(hours=5, minutes=30))


def get_weather_by_coords(lat, lon):
  try:
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    w_res = requests.get(w_url, timeout=5).json()
    return round(float(w_res["current_weather"]["temperature"]), 1)
  except:
    return 35.0


def get_nearby_structures(lat, lon, df, max_dist=50):
  if (
      df is None
      or "Latitude" not in df.columns
      or "Longitude" not in df.columns
  ):
    return []
  lat1, lon1 = math.radians(lat), math.radians(lon)
  lat2, lon2 = np.radians(df["Latitude"]), np.radians(df["Longitude"])
  dlat = lat2 - lat1
  dlon = lon2 - lon1
  a = (
      np.sin(dlat / 2.0) ** 2
      + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
  )
  c = 2 * np.arcsin(np.sqrt(a))
  distance_meters = 6367 * c * 1000

  df_temp = df.copy()
  df_temp["Calculated_Dist"] = distance_meters
  nearby = df_temp[df_temp["Calculated_Dist"] <= max_dist].sort_values(
      "Calculated_Dist"
  )

  results = []
  for _, row in nearby.iterrows():
    results.append(
        {
            "Structure_No": str(row["Structure_No"]),
            "Tension_Length": float(row["Tension_Length"]),
            "Distance": round(float(row["Calculated_Dist"]), 1),
        }
    )
  return results


def main(page: ft.Page):
  page.title = "OHE ATD Smart Tool"
  page.theme_mode = ft.ThemeMode.DARK
  page.bgcolor = "#050a0f"
  page.vertical_alignment = ft.MainAxisAlignment.START
  page.padding = 15
  page.scroll = ft.ScrollMode.AUTO

  # Load data
  @ft.app_data
  def load_data():
    try:
      df_old = pd.read_csv(OLD_SHEET_URL)
      df_old.columns = df_old.columns.str.strip()
    except:
      df_old = None

    try:
      df_gis = pd.read_csv(NEW_SHEET_URL)
      df_gis.columns = df_gis.columns.str.strip()
    except:
      df_gis = None
    return df_old, df_gis

  df_old, df_gis = load_data()

  # UI Elements
  title_text = ft.Text(
      "⚡ OHE ATD Smart Tool",
      size=24,
      weight=ft.FontWeight.BOLD,
      color="#00d4ff",
      text_align=ft.TextAlign.CENTER,
  )

  mode_tabs = ft.Tabs(
      selected_index=0,
      animation_duration=300,
      tabs=[
          ft.Tab(text="Manual Mode"),
          ft.Tab(text="GIS Mode"),
      ],
      expand=False,
  )

  # Containers for modes
  manual_content = ft.Column()
  gis_content = ft.Column()

  # --- MANUAL MODE SETUP ---
  struct_options = (
      ["Manual Entry"] + df_old["Structure_No"].dropna().unique().tolist()
      if df_old is not None
      else ["Manual Entry"]
  )
  m_struct_dropdown = ft.Dropdown(
      label="📍 Select Structure No",
      options=[ft.dropdown.Option(s) for s in struct_options],
      value="Manual Entry",
      border_color="#00d4ff",
      label_style=ft.TextStyle(color="#00d4ff"),
  )
  m_length_input = ft.TextField(
      label="Tension Length (L) in meters",
      value="750.0",
      border_color="#00d4ff",
  )
  m_temp_input = ft.TextField(
      label="Current Temp (°C)", value="35.0", border_color="#00d4ff"
  )

  m_result_x = ft.Text("X (Pulley Gap): -- mm", size=18, color="#00ff41", weight=ft.FontWeight.BOLD)
  m_result_y = ft.Text("Y (Weight Height): -- mm", size=18, color="#00ff41", weight=ft.FontWeight.BOLD)

  def calculate_manual(e):
    try:
      L = float(m_length_input.value)
    except:
      L = 750.0
    try:
      t2 = float(m_temp_input.value)
    except:
      t2 = 35.0

    delta = L * 0.000017 * (35 - t2) * 1000
    x = 1300 + delta
    y = 2300 + (3 * delta)
    m_result_x.value = f"X (Pulley Gap): {round(x, 1)} mm"
    m_result_y.value = f"Y (Weight Height): {round(y, 1)} mm"
    page.update()

  m_calc_btn = ft.ElevatedButton(
      text="Calculate ATD",
      bgcolor="#00d4ff",
      color="black",
      on_click=calculate_manual,
  )

  manual_content.controls = [
      m_struct_dropdown,
      m_length_input,
      m_temp_input,
      m_calc_btn,
      ft.Divider(),
      m_result_x,
      m_result_y,
  ]

  # --- GIS MODE SETUP ---
  gis_status = ft.Text("Status: Ready for GPS Sync", color="#00d4ff", size=14)
  g_temp_input = ft.TextField(
      label="Current Temp (°C)", value="35.0", border_color="#00d4ff"
  )
  g_result_x = ft.Text("X (Pulley Gap): -- mm", size=18, color="#00ff41", weight=ft.FontWeight.BOLD)
  g_result_y = ft.Text("Y (Weight Height): -- mm", size=18, color="#00ff41", weight=ft.FontWeight.BOLD)

  def sync_gps_action(e):
    # Simulated/Placeholder GPS for demo or mobile integration
    gis_status.value = "Status: GPS Synced Successfully (Sample Coordinates)"
    g_temp_input.value = "32.5"
    page.update()

  gis_sync_btn = ft.ElevatedButton(
      text="🚀 Auto-Sync GPS & Weather",
      bgcolor="#00d4ff",
      color="black",
      on_click=sync_gps_action,
  )

  gis_content.controls = [
      gis_sync_btn,
      gis_status,
      g_temp_input,
      ft.Divider(),
      g_result_x,
      g_result_y,
  ]

  body_container = ft.Container(content=manual_content, padding=10)

  def tab_changed(e):
    if mode_tabs.selected_index == 0:
      body_container.content = manual_content
    else:
      body_container.content = gis_content
    page.update()

  mode_tabs.on_change = tab_changed

  page.add(
      title_text,
      ft.Divider(),
      mode_tabs,
      body_container,
      ft.Text(
          "DEVELOPED BY: A.K.MULCHANDANI JE/TRD",
          size=10,
          color="grey",
          text_align=ft.TextAlign.CENTER,
      ),
  )


ft.app(target=main)from datetime import datetime, timezone, timedelta
import io
import math
import flet as ft
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import requests

# Google Sheet URLs
OLD_SHEET_ID = "1vfioGSmpC7a5S8SMUpCk9xn-mtttvcTecLEQ1Sd6XkU"
OLD_SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{OLD_SHEET_ID}/export?format=csv"
)

NEW_SHEET_ID = "1VYubXUbniIrCNZlybPQD8lC71SS2wBYlR-kF_EtD5IY"
NEW_SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{NEW_SHEET_ID}/export?format=csv"
)

ist_offset = timezone(timedelta(hours=5, minutes=30))


def get_weather_by_coords(lat, lon):
  try:
    w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    w_res = requests.get(w_url, timeout=5).json()
    return round(float(w_res["current_weather"]["temperature"]), 1)
  except:
    return 35.0


def get_nearby_structures(lat, lon, df, max_dist=50):
  if (
      df is None
      or "Latitude" not in df.columns
      or "Longitude" not in df.columns
  ):
    return []
  lat1, lon1 = math.radians(lat), math.radians(lon)
  lat2, lon2 = np.radians(df["Latitude"]), np.radians(df["Longitude"])
  dlat = lat2 - lat1
  dlon = lon2 - lon1
  a = (
      np.sin(dlat / 2.0) ** 2
      + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
  )
  c = 2 * np.arcsin(np.sqrt(a))
  distance_meters = 6367 * c * 1000

  df_temp = df.copy()
  df_temp["Calculated_Dist"] = distance_meters
  nearby = df_temp[df_temp["Calculated_Dist"] <= max_dist].sort_values(
      "Calculated_Dist"
  )

  results = []
  for _, row in nearby.iterrows():
    results.append(
        {
            "Structure_No": str(row["Structure_No"]),
            "Tension_Length": float(row["Tension_Length"]),
            "Distance": round(float(row["Calculated_Dist"]), 1),
        }
    )
  return results


def main(page: ft.Page):
  page.title = "OHE ATD Smart Tool"
  page.theme_mode = ft.ThemeMode.DARK
  page.bgcolor = "#050a0f"
  page.vertical_alignment = ft.MainAxisAlignment.START
  page.padding = 15
  page.scroll = ft.ScrollMode.AUTO

  # Load data
  @ft.app_data
  def load_data():
    try:
      df_old = pd.read_csv(OLD_SHEET_URL)
      df_old.columns = df_old.columns.str.strip()
    except:
      df_old = None

    try:
      df_gis = pd.read_csv(NEW_SHEET_URL)
      df_gis.columns = df_gis.columns.str.strip()
    except:
      df_gis = None
    return df_old, df_gis

  df_old, df_gis = load_data()

  # UI Elements
  title_text = ft.Text(
      "⚡ OHE ATD Smart Tool",
      size=24,
      weight=ft.FontWeight.BOLD,
      color="#00d4ff",
      text_align=ft.TextAlign.CENTER,
  )

  mode_tabs = ft.Tabs(
      selected_index=0,
      animation_duration=300,
      tabs=[
          ft.Tab(text="Manual Mode"),
          ft.Tab(text="GIS Mode"),
      ],
      expand=False,
  )

  # Containers for modes
  manual_content = ft.Column()
  gis_content = ft.Column()

  # --- MANUAL MODE SETUP ---
  struct_options = (
      ["Manual Entry"] + df_old["Structure_No"].dropna().unique().tolist()
      if df_old is not None
      else ["Manual Entry"]
  )
  m_struct_dropdown = ft.Dropdown(
      label="📍 Select Structure No",
      options=[ft.dropdown.Option(s) for s in struct_options],
      value="Manual Entry",
      border_color="#00d4ff",
      label_style=ft.TextStyle(color="#00d4ff"),
  )
  m_length_input = ft.TextField(
      label="Tension Length (L) in meters",
      value="750.0",
      border_color="#00d4ff",
  )
  m_temp_input = ft.TextField(
      label="Current Temp (°C)", value="35.0", border_color="#00d4ff"
  )

  m_result_x = ft.Text("X (Pulley Gap): -- mm", size=18, color="#00ff41", weight=ft.FontWeight.BOLD)
  m_result_y = ft.Text("Y (Weight Height): -- mm", size=18, color="#00ff41", weight=ft.FontWeight.BOLD)

  def calculate_manual(e):
    try:
      L = float(m_length_input.value)
    except:
      L = 750.0
    try:
      t2 = float(m_temp_input.value)
    except:
      t2 = 35.0

    delta = L * 0.000017 * (35 - t2) * 1000
    x = 1300 + delta
    y = 2300 + (3 * delta)
    m_result_x.value = f"X (Pulley Gap): {round(x, 1)} mm"
    m_result_y.value = f"Y (Weight Height): {round(y, 1)} mm"
    page.update()

  m_calc_btn = ft.ElevatedButton(
      text="Calculate ATD",
      bgcolor="#00d4ff",
      color="black",
      on_click=calculate_manual,
  )

  manual_content.controls = [
      m_struct_dropdown,
      m_length_input,
      m_temp_input,
      m_calc_btn,
      ft.Divider(),
      m_result_x,
      m_result_y,
  ]

  # --- GIS MODE SETUP ---
  gis_status = ft.Text("Status: Ready for GPS Sync", color="#00d4ff", size=14)
  g_temp_input = ft.TextField(
      label="Current Temp (°C)", value="35.0", border_color="#00d4ff"
  )
  g_result_x = ft.Text("X (Pulley Gap): -- mm", size=18, color="#00ff41", weight=ft.FontWeight.BOLD)
  g_result_y = ft.Text("Y (Weight Height): -- mm", size=18, color="#00ff41", weight=ft.FontWeight.BOLD)

  def sync_gps_action(e):
    # Simulated/Placeholder GPS for demo or mobile integration
    gis_status.value = "Status: GPS Synced Successfully (Sample Coordinates)"
    g_temp_input.value = "32.5"
    page.update()

  gis_sync_btn = ft.ElevatedButton(
      text="🚀 Auto-Sync GPS & Weather",
      bgcolor="#00d4ff",
      color="black",
      on_click=sync_gps_action,
  )

  gis_content.controls = [
      gis_sync_btn,
      gis_status,
      g_temp_input,
      ft.Divider(),
      g_result_x,
      g_result_y,
  ]

  body_container = ft.Container(content=manual_content, padding=10)

  def tab_changed(e):
    if mode_tabs.selected_index == 0:
      body_container.content = manual_content
    else:
      body_container.content = gis_content
    page.update()

  mode_tabs.on_change = tab_changed

  page.add(
      title_text,
      ft.Divider(),
      mode_tabs,
      body_container,
      ft.Text(
          "DEVELOPED BY: A.K.MULCHANDANI JE/TRD",
          size=10,
          color="grey",
          text_align=ft.TextAlign.CENTER,
      ),
  )


ft.app(target=main)
