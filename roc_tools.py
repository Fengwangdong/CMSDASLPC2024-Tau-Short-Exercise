from __future__ import print_function

import ROOT
from ROOT import gROOT, gStyle, TEfficiency
from cms_style import cms_style

cms_style(gStyle)

hex_colours = ['#7fc97f','#beaed4','#fdc086','#386cb0','#f0027f','#bf5b17','#666666','#ffff99'] # dark
colours = [ROOT.TColor.GetColor(hex) for hex in hex_colours]
markers = [20, 21, 22, 23, 24, 25, 26, 27]


def hists_to_roc(hsig, hbg, w_error=False):
    '''Produce ROC curve from 2 input histograms hsig and hbg.
    Partly adapted from Giovanni's ttH code.
    '''
    nbins = hsig.GetNbinsX() + 2 # include under/overflow; remove events not passing selection
    si = [hsig.GetBinContent(i) for i in range(nbins)]
    bi = [hbg.GetBinContent(i) for i in range(nbins)]

    if hsig.GetMean() > hbg.GetMean():
        si.reverse()
        bi.reverse()

    sums, sumb = sum(si), sum(bi)
    if sums == 0 or sumb == 0:
        print('WARNING: Either signal or background histogram empty', sums, sumb)
        return None

    # make cumulative
    for i in range(1, nbins):
        si[i] += si[i - 1]
        bi[i] += bi[i - 1]
    fullsi, fullbi = si[:], bi[:]
    si, bi = [], []
    for i in range(1, nbins):
        # skip negative weights
        if si and (fullsi[i] < si[-1] or fullbi[i] < bi[-1]):
            continue
        # skip repetitions
        if fullsi[i] != fullsi[i - 1] or fullbi[i] != fullbi[i - 1]:
            si.append(fullsi[i])
            bi.append(fullbi[i])

    # Remove the trivial (1, 1) points
    si.pop()
    bi.pop()

    if len(si) == 2:
        si = [si[0]]
        bi = [bi[0]]

    bins = len(si)

    if not w_error:
        roc = ROOT.TGraph(bins)
        for i in range(bins):
            roc.SetPoint(i, si[i] / sums, bi[i] / sumb)

        return roc

    roc = ROOT.TGraphAsymmErrors(bins)
    for i in range(bins):
        interval = 0.683

        e_s_low = si[i] / sums - TEfficiency.ClopperPearson(sums, si[i], interval, False)
        e_s_up = TEfficiency.ClopperPearson(sums, si[i], interval, True) - si[i] / sums
        e_b_low = bi[i] / sumb - TEfficiency.ClopperPearson(sumb, bi[i], interval, False)
        e_b_up = TEfficiency.ClopperPearson(sumb, bi[i], interval, True) - bi[i] / sumb

        roc.SetPoint(i, si[i] / sums, bi[i] / sumb)
        roc.SetPointError(i, e_s_low, e_s_up, e_b_low, e_b_up)

    return roc


def make_legend(rocs, textSize=0.035, left=True):
    (x1, y1, x2, y2) = (.18 if left else .68, .76 - textSize * max(len(rocs) - 3, 0), .4 if left else .95, .88)
    leg = ROOT.TLegend(x1, y1, x2, y2)
    leg.SetFillColor(0)
    leg.SetShadowColor(0)
    leg.SetLineColor(0)
    leg.SetLineWidth(0)
    leg.SetTextFont(42)
    leg.SetTextSize(textSize)
    for key, roc in rocs:
        leg.AddEntry(roc, key, 'lp')
    leg.Draw()

    return leg


def make_roc_plot(rocs, set_name='rocs', ymin=0., ymax=1., xmin=0., xmax=1., logy=False, formats=[]):
    '''Plots multiple ROC curves (TGraph derivatives)
    '''
    allrocs = ROOT.TMultiGraph(set_name, '')
    point_graphs = []
    i_marker = 0
    for i_col, graph in enumerate(rocs):
        col = colours[i_col]
        graph.SetLineColor(col)
        graph.SetMarkerColor(col)
        graph.SetLineWidth(3)
        graph.SetMarkerStyle(0)
        if graph.GetN() > 10:
            allrocs.Add(graph)
        else:
            graph.SetMarkerStyle(markers[i_marker])
            i_marker += 1
            graph.SetMarkerSize(1)
            point_graphs.append(graph)

    c = ROOT.TCanvas()

    allrocs.Draw('APL')

    allrocs.GetXaxis().SetTitle('#epsilon_{s}')
    allrocs.GetYaxis().SetTitle('#epsilon_{b}')
    allrocs.GetYaxis().SetDecimals(True)

    allrocs.GetYaxis().SetRangeUser(ymin, ymax)
    allrocs.GetXaxis().SetRangeUser(xmin, xmax)
    if logy:
        if ymin > 0.:
            c.SetLogy()
        else:
            print('Cannot set logarithmic y axis if minimum y value is <= 0.')

    allrocs.Draw('APL')

    for graph in point_graphs:
        graph.Draw('P')

    allrocs.leg = make_legend(list(zip([r.title for r in rocs], rocs)))

    for f in formats:
        c.Print(set_name + '.' + f)

    return allrocs, c
