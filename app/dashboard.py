# =======================================================
# Author: Max Pinheiro Jr <max.pinheiro-jr@univ-amu.fr>
# Date: September 20 2021
# =======================================================
import base64
import py3Dmol
import requests

from io import BytesIO

import ase
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go

st.set_page_config(page_title="WS22 database", layout="wide")

padding = 3
st.markdown(f""" <style>
    .reportview-container .main .block-container{{
        padding-top: {padding}rem;
        padding-right: {padding}rem;
        padding-left: {padding}rem;
        padding-bottom: {padding}rem;
    }} </style> """, unsafe_allow_html=True)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        width: 275px;
    }
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
        width: 275px;
        margin-left: -275px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("WS22 database: towards configurationally diverse molecular datasets")
st.write('---')

st.write("""
         This dashboard was designed to explore the main statistical features of the WS22 database.
         The WS22 database is composed of 10 independent molecular datasets exploring a broad region
         of the configurational space of small to medium-sized flexible organic molecules characterized
         by multiple stable conformations. Which one cof the datasets contain 120K molecular geometries
         generated by combining a Wigner sampling approach (100k points) together with a geodesic
         interpolation between all pairs of conformations (20k points). These datasets also include 
         several quantum chemical properties calculated at the density functional theory level.
         """)

@st.cache(allow_output_mutation=True, show_spinner=False)
def get_data_zenodo(molecule):
    molecule = molecule.lower().replace('2-','')
    filename = 'ws22_' + molecule + '.npz'
    zenodo_data_path = f'https://zenodo.org/record/7032334/files/{filename}?download=1'
    response = requests.get(zenodo_data_path)
    response.raise_for_status()
    data = dict(np.load(BytesIO(response.content)))
    return data

@st.cache
def load_data(molecule):
    molecule = molecule.lower().replace('2-','')
    base_dir = '../final_datasets/'
    filename = base_dir + 'ws22_' + molecule + '.npz'
    data = dict(np.load(filename))
    return data

st.sidebar.markdown("## List of available datasets")
molecules = ('acrolein', 'alanine', 'DMABN', '2-nitrophenol', 'o-HBDI',
             'SMA', 'thymine', 'toluene', 'urea', 'urocanic')
dataset_name = st.sidebar.selectbox('Select molecule', molecules)

data = get_data_zenodo(dataset_name)
#data = load_data(dataset_name)
conf = data['CONF'].flatten()

def z_to_labels(dataset):
    atom_types = {1:'H', 6:'C', 7:'N', 8:'O'}
    Z = dataset['Z'].flatten()
    labels = np.vectorize(atom_types.get)(Z)
    return labels

def process_mulliken_data(dataset):
    n_atoms = dataset['Q'].shape[1]
    atom_labels = z_to_labels(dataset)

    atom_charges = dataset['Q'].reshape(-1,n_atoms)
    col_names = [atom_labels[i] + str(i+1) for i in range(n_atoms)]
    df = pd.DataFrame(atom_charges, columns = col_names)
    df['Conformation'] = conf
    df = pd.melt(df, id_vars='Conformation', 
                 var_name='atom_labels', 
                 value_name='Mulliken charges')
    atom_labels = ['None'] + np.unique(atom_labels).tolist()
    atom_type_filter = st.sidebar.radio(label="Atom type filter", 
                                        options = atom_labels)
    if atom_type_filter != 'None':
       df = df[df['atom_labels'].str.contains(atom_type_filter)]
    return df

def process_force_data(dataset):
    atom_labels = z_to_labels(dataset)
    fnorm_types = {'total': [0,1,2], 'Fx': [0], 'Fy': [1], 'Fz': [2]}
    radio_selection = st.sidebar.radio(label="Select component", options = list(fnorm_types.keys()))
    forces = dataset['F'][:,:,fnorm_types.get(radio_selection)]
    forces_norm = np.linalg.norm(forces,axis=(1,2))
    df = pd.DataFrame({'Forces': forces_norm, 
                       'Conformation': conf})
    return df

def process_dipole_data(dataset):
    dipoles = dataset['DP']
    options = {'total': np.linalg.norm(dipoles, axis=1),
               'Dx': dipoles[:,0], 'Dy': dipoles[:,1],
               'Dz': dipoles[:,2]}
    radio_selection = st.sidebar.radio(label="Select component", options = list(options.keys()))
    dipoles = options.get(radio_selection)
    df = pd.DataFrame({'Dipole moment': dipoles, 'Conformation': conf})
    return df

def process_quadrupole_data(dataset):
    quadrupoles = dataset['QP']
    options = {'norm': np.linalg.norm(quadrupoles,axis=(1,2)),
               'XX': quadrupoles[:,0,0], 'YY': quadrupoles[:,1,1],
               'ZZ': quadrupoles[:,2,2], 'XY': quadrupoles[:,0,1],
               'XZ': quadrupoles[:,0,2], 'YZ': quadrupoles[:,1,2]}
    radio_selection = st.sidebar.radio(label="Select component", options = list(options.keys()))
    quadrupoles = options.get(radio_selection)
    df = pd.DataFrame({'Quadrupole moment': quadrupoles, 'Conformation': conf})
    return df

def process_polar_data(dataset):
    polar = dataset['P']
    df = pd.DataFrame(polar)
    df['Conformation'] = conf
    df = pd.melt(df, id_vars='Conformation',
                 var_name='components',
                 value_name='Polarizability')
    return df

def process_freq_data(dataset):
    freq = dataset['FREQ']
    n_modes = freq.shape[1]
    df = pd.DataFrame(freq)
    df['Conformation'] = conf
    df = pd.melt(df, id_vars='Conformation',
                 var_name='modes',
                 value_name='Vibrational frequencies')
    select_mode = st.sidebar.slider("mode selector", min_value=-0, max_value=n_modes, 
                                    value=0, step=1)
    df = df[df['modes'] == select_mode]
    return df

def process_thermal_data(dataset):
    eth = dataset['ETH']
    energy_types = ['energies', 'enthalpies', 'free energies']
    df = pd.DataFrame(eth, columns=energy_types)
    df['Conformation'] = conf
    df = pd.melt(df, id_vars='Conformation',
                 var_name='types',
                 value_name='Electronic + thermal')
    check_boxes = [st.sidebar.checkbox(en, key=en) for en in energy_types]
    energy_types = np.array(energy_types)
    selected_types = energy_types[check_boxes].tolist()
    df = df[df['types'].isin(selected_types)]
    return df

def data_to_plot(property):
    if property == 'Potential energy':
       epot = (data['E'] - data['E'].min()).flatten()
       df = pd.DataFrame({'Potential energy': epot})
    elif property == 'Forces':
       df = process_force_data(data)
    elif property == 'Mulliken charges':
       df = process_mulliken_data(data)
    elif property == 'Dipole moment':
       df = process_dipole_data(data)
    elif property == 'Quadrupole moment':
       df = process_quadrupole_data(data)
    elif property == 'Polarizability':
       df = process_polar_data(data)
    elif property == 'HOMO-LUMO gap':
       egap = data['HL'][:,1] - data['HL'][:,0]
       df = pd.DataFrame({'HOMO-LUMO gap': egap})
    elif property == 'Electronic spatial extent':
       r2 = data['R2'].flatten()
       df = pd.DataFrame({'Electronic spatial extent': r2})

    if 'Conformation' not in df.columns.tolist():
       df['Conformation'] = conf

    return df

def create_xyz(dataset, index):
    atom_labels = z_to_labels(dataset)
    n_atoms = len(atom_labels)
    geoms_array = dataset['R'][[index]][0:n_atoms,:]
    geoms_string = ""
    comment_line = ""
    mask = '{:<6s} {:12.8f} {:12.8f} {:12.8f} \n'

    for n, xyz in enumerate(geoms_array):
        geoms_string += str(n_atoms) + "\n" + comment_line + "\n"
        for l, atom_coords in zip(atom_labels, xyz):
            geoms_string += mask.format(l,*atom_coords)
    return geoms_string

def view_molecule(dataset, index, style):

    geom = create_xyz(dataset,index)

    molview = py3Dmol.view(width=330,height=330)
    molview.addModel(geom,'xyz')

    molview.setViewStyle({'style':'outline','color':'black','width':0.02})
    molview.setStyle(style)
    #molview.setBackgroundColor('#e7e7e7')
    molview.setBackgroundColor('#e2e2e2')
    molview.zoomTo()
    hover_func = """
    function(atom,viewer) {
       if(!atom.label) {
           atom.label = viewer.addLabel(atom.atom+atom.serial,
               {position: atom, backgroundColor: 'mintcream', fontColor:'black'});
       }
    }"""
    unhover_func = """
    function(atom,viewer) {
       if(atom.label) {
         viewer.removeLabel(atom.label);
         delete atom.label;
       }
    }"""
    molview.setHoverable({}, True, hover_func, unhover_func)

    return (geom, molview)

def get_internal_coords(coords, labels, indices):
    int_coords = []
    for xyz in coords:
        mol = ase.Atoms(symbols=labels, positions=xyz)
        if len(indices) == 4:
           var = mol.get_dihedral(*indices)
           if var > 180:
              var = 360 - var
        elif len(indices) == 3:
           var = mol.get_angle(*indices)
        elif len(indices) == 2:
           var = mol.get_distance(*indices)
        else:
           error_msg = "Invalid atoms selection!\n"
           error_msg += "The number of indices must be 2 (distance), 3 (angle) or 4 (dihedral)."
           raise ValueError(error_msg)
        int_coords.append(var)
    int_coords = np.array(int_coords)
    return int_coords

@st.cache(allow_output_mutation=True, show_spinner=False)
def build_ic_dataframe(dataset, selected_coords):
    df = pd.DataFrame()
    ic_types = {2: 'distance', 3: 'angle', 4: 'dihedral'}
    for ic in selected_coords:
        atom_indices = [int(i) for i in ic.strip().split(',')]
        n_atoms = len(atom_indices)
        with st.spinner(f"Computing {ic_types.get(n_atoms)} for atoms {ic}..."):
             atom_labels = z_to_labels(dataset)
             values = get_internal_coords(dataset['R'], atom_labels, atom_indices)
             atom_labels = atom_labels[atom_indices].tolist()
             labels = [''.join([a,str(b)]) for a,b in zip(atom_labels,atom_indices)]
             col_name = '-'.join(labels)
             df[col_name] = values
    df['Conformation'] = conf
    return df

def geom_downloader(geom_string, molecule, index):
    b64 = base64.b64encode(geom_string.encode()).decode()
    new_filename = "{}_geom_{}.xyz".format(molecule, idx)
    href = f'<a href="data:file/txt;base64,{b64}" download="{new_filename}">Click here to download!</a>'
    st.markdown(href,unsafe_allow_html=True)

def build_stats(dataframe, feature):
    df_confs = dataframe[[feature, 'Conformation']].groupby('Conformation')
    _median = df_confs.median().reset_index()[feature].values
    df_stats = df_confs.describe().unstack(1).reset_index()
    df_stats = df_stats.pivot(index='Conformation', values=0, columns='level_1')
    df_stats['median'] = _median
    return df_stats

properties = ('Potential energy', 'Forces', 'Mulliken charges', 'Dipole moment', 'Quadrupole moment',
              'Polarizability', 'HOMO-LUMO gap', 'Electronic spatial extent')
property_name = st.sidebar.selectbox('Select property', properties)

df = data_to_plot(property_name)

col1, col2 = st.columns([2,1])

with col1:
    tabs = st.tabs(["📈 statistics", "📏 geometry"])

    tab_stats, tab_geoms = tabs

    with tab_stats:
        st.subheader("Data distribution:")
        fig = px.histogram(df, x=property_name, color="Conformation",
                           opacity=0.7, marginal="box", # or violin, rug
                           barmode="overlay", # histfunc="count", histnorm="density",
                           hover_data=df.columns)
        fig.update_layout(showlegend=True, width=650, height=480,
                          margin=dict(l=1,r=1,b=1,t=1),
                          font=dict(color='#383635', size=16),
                          plot_bgcolor='#e7e7e7',
                          paper_bgcolor='#e7e7e7')

        st.write(fig)

        if len(df.index) != 0:
           df_stats = build_stats(df, property_name)
           st.dataframe(df_stats)

    with tab_geoms:
        st.subheader("Analysis of internal coordinates:")
        selected_coords = st.text_input('Atom indices (comma separated):', '1,0,2,3')
        st.write("Hint: Check the atom indices in the molecule viewer (left panel), and use a dash symbol '-' to select multiple coordinates.")
        selected_coords = selected_coords.split('-')
        df = build_ic_dataframe(data, selected_coords)
        computed_coords = df.drop(['Conformation'], axis=1).columns.tolist()
        coords_name = st.sidebar.selectbox('Select coordinate', computed_coords)
        fig = px.histogram(df, x=coords_name, color="Conformation",
                           opacity=0.7, marginal="box", barmode="overlay",
                           hover_data=df.columns)
        fig.update_layout(showlegend=True, width=650, height=480,
                          margin=dict(l=1,r=1,b=1,t=1),
                          font=dict(color='#383635', size=16),
                          plot_bgcolor='#e7e7e7',
                          paper_bgcolor='#e7e7e7')

        st.write(fig)

        if len(df.index) != 0:
           df_stats = build_stats(df, coords_name)
           st.dataframe(df_stats)


with col2:
    st.write('')
    st.write('')
    st.write('')
    st.subheader("Molecule viewer:")
    max_num_geoms = data['R'].shape[0]
    idx = st.slider("geometry index", min_value=1, max_value=max_num_geoms,
                    value=1, step=1)
    s = {'stick': {'radius': .15}, 'sphere': {'scale': 0.20}}
    xyz_geom, mol = view_molecule(data, idx-1, s)
    mol.render()
    t = mol.js()
    viz_html = t.startjs + "\n" + t.endjs

    st.components.v1.html(viz_html, width=338, height=338)

    xyz_filename = filename = "{}_geom_{}.xyz".format(dataset_name, idx)
    st.download_button("Download XYZ", xyz_geom, xyz_filename)

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden; }
        footer {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

with st.expander("📓: Computational details"):
     st.markdown(
                 "* Geometries generation: Wigner sampling + Geometry interpolation\n"
                 "* Quantum chemical calculations: Gaussian09 program\n"
                 "* Density functional: PBE0 \n"
                 "* Basis set: 6-311G* "
                )

citation_info = "Max Pinheiro Jr, Shuang Zhang, Pavlo O. Dral, & Mario Barbatti. (2022). WS22 database: combining Wigner Sampling and geometry interpolation towards\
                 configurationally diverse molecular datasets (1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.7032334"

st.markdown("### Citation 📖")
st.info(citation_info)

st.markdown("### Contacts")

"""
[![Twitter Follow](https://img.shields.io/twitter/follow/max_jr?label=Follow)](https://twitter.com/max_jr)
[![MAIL Badge](https://img.shields.io/badge/-max.pinheiro--jr%40univ--amu.fr-red?style=flat-square&logo=Gmail&logoColor=white&link=mailto:max.pinheiro-jr@univ-amu.fr)](mailto:max.pinheiro-jr@univ-amu.fr)

(C) Max Pinheiro Jr, 2021-2022
"""
