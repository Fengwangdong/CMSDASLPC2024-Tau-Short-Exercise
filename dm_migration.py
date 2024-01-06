import argparse

from ROOT import gStyle, TCanvas, TH2F, TFile

from cms_style import cms_style
cms_style(gStyle)
gStyle.SetTitleOffset(1.65, "Y")
gStyle.SetPadLeftMargin(0.20)

def dm_migration(tree, tau_decayMode_string=None, labels=None, gen_cut='tau_gen_pt>20 && abs(tau_gen_eta)<2.3', title='', formats=[]):
    '''Creates a decay mode migration plot.
    Parameters:
        tree (ROOT TTree): input tree
        tau_decayMode_string (str): draw expression that maps the decay modes onto ints 
                             (-2: undefined, used only for reco axis)
                             (-1 and following: regular decay modes)
        labels (list of str): labels for
        title (str): title used for output plot
        formats (list of str): picture formats used for output plot

    '''
    if not tau_decayMode_string:
        tau_decayMode_string = ('-2'
                         '+ (tau_pt>20 && tau_decayMode>=0 && tau_decayMode <200)*(1 ' # will contain reco DM 5 and 6 and other gen DMs
                            '+ (tau_decayMode==0)'
                            '+ 2*(tau_decayMode==1||tau_decayMode==2)'
                            '+ 3*(tau_decayMode==10)'
                            '+ 4*(tau_decayMode==11))'
            )


    if not labels:
        labels = ['None', 'Other', '#pi', '#pi#pi^{0}s', '#pi#pi#pi', '#pi#pi#pi#pi^{0}s']

    canvas = TCanvas('decay_mode_matrix')

    n_l = len(labels)
    h_migration = TH2F('migration{}'.format(title), '', n_l-1, -1., n_l-2., n_l, -2, n_l-2.)
    tree.Project(h_migration.GetName(), tau_decayMode_string+':'+tau_decayMode_string.replace('tau_', 'tau_gen_'), gen_cut)

    for y_bin in range(1, h_migration.GetYaxis().GetNbins()+1):
        h_migration.GetYaxis().SetBinLabel(y_bin, labels[y_bin-1])
    for x_bin in range(1, h_migration.GetXaxis().GetNbins()+1):
        h_migration.GetXaxis().SetBinLabel(x_bin, labels[x_bin])

    h_migration.GetYaxis().SetTitle('Offline DM')
    h_migration.GetXaxis().SetTitle('Generated DM')

    for x_bin in range(1, h_migration.GetNbinsX()+1):
        int_y = sum(h_migration.GetBinContent(x_bin, y_bin) for y_bin in range(1, h_migration.GetNbinsY()+1))
        if int_y == 0.:
            int_y = 1.
        for y_bin in range(1, h_migration.GetNbinsY()+1):
            h_migration.SetBinContent(x_bin, y_bin, h_migration.GetBinContent(x_bin, y_bin)/int_y)

    h_migration.Draw('TEXT')
    h_migration.SetMarkerColor(1)
    h_migration.SetMarkerSize(2.2)
    gStyle.SetPaintTextFormat("1.2f")

    for f in formats:
        canvas.Print(f'dm_migration_{title}.{f}')

    canvas.keeper = h_migration

    return canvas


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--inputFile', default='Myroot_CMSSW_9_4_0_pre2_PU25ns_94X_mc2017_realistic_v1-v1_ZTT.root', help='Input file name')
    parser.add_argument('-l', '--label', default='standard', help='Label for plot output')
    parser.add_argument('-t', '--treeName', default='per_tau', help='Name of TTree in file')
    args = parser.parse_args()

    title = args.label
    f_in = TFile.Open(args.inputFile)
    tree = f_in.Get(args.treeName)
    dm_migration(tree, title=title, formats=['png'])

    