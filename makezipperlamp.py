import rhinoscriptsyntax as rs
import random

base_srfs = rs.ObjectsByLayer("base")
base_edges = rs.ObjectsByLayer("edges")
associated_edges = {}
completed_pieces = []

def makeZipperLamp():
	# color edges
	for e in base_edges:
		rs.ObjectColor(e,[random.randrange(0,255),random.randrange(0,255),random.randrange(0,255)])
		rs.ObjectName(e,"0")
	for bs in base_srfs:
		associate(bs)
	ind = 0
	for bs in base_srfs:
		laydownSurface(bs, ind)
		ind += 1

	at = 0.0
	#for cp in completed_pieces:
	#	bb = rs.BoundingBox(cp)
	#	w = rs.VectorSubtract(bb[1],bb[0])[0]
	#	rs.MoveObject(cp, [at-bb[0][0],0-bb[0][1],0])
	#	at += w

def associate(bs):
	rs.AddLayer("construction")
	rs.CurrentLayer("construction")

	edges = []
	for be in base_edges:
		good_int = False
		ints = rs.CurveBrepIntersect(be, bs, 0.01)
		if ints != None:
			for i in ints:
				if i != []:
					for si in i:
						if rs.IsCurve(si) == True: good_int = True
						rs.DeleteObject(si)
		if good_int == True: edges.append(be)

	associated_edges[bs] = edges

def laydownSurface(bs, ind):
	lname = "face "+str(ind)
	print(lname)
	rs.AddLayer(lname)
	rs.CurrentLayer(lname)
	result = rs.UnrollSurface(bs, False, associated_edges[bs])

	face = result[0]
	edges = result[1]

	cen = rs.SurfaceAreaCentroid(face)[0]
	ind = 0
	for e in edges:
		if rs.IsCurve(e):
			rs.ObjectColor(e,rs.ObjectColor(associated_edges[bs][ind]))
			strdir = rs.ObjectName( associated_edges[bs][ind])
			makeZipper(e, cen, face, int(strdir), rs.CurveLength(associated_edges[bs][ind]))
			rs.ObjectName( associated_edges[bs][ind],str(int(strdir)+1))
			ind = ind + 1

	#rs.DeleteObject(face)

	eobjs = rs.ObjectsByLayer(lname)
	ecrvs = []
	for eobj in eobjs:
		if rs.IsCurve(eobj): ecrvs.append(eobj)
	cp = rs.JoinCurves(ecrvs,True)
	completed_pieces.append(cp[0])

def makeZipper(e, cen, face, direction, len3d):
	segs = int(len3d)*5
	params = rs.DivideCurve(e, segs, False, False)

	rs.SelectObject(e)

	ept = rs.EvaluateCurve(e, rs.CurveClosestPoint(e, cen))

	os_sc = 0.0
	if (direction > 0): os_sc = 1.0

	for ind in range(0, len(params)-1):
		os = 0.2
		# make line seg
		p0 = params[ind]
		p1 = params[ind+1]
		pm = p0 + (p1-p0)*0.5
		seg = rs.AddSubCrv(e, p0, p1)
		# offset
		pt = rs.EvaluateCurve(e, pm)
		tan = rs.CurveTangent(e, pm)
		norm = rs.VectorRotate(tan, 90, [0,0,1])*os
		os_pt = pt+norm

		pt0 = rs.EvaluateCurve(e, p0)
		tan0 = rs.CurveTangent(e, p0)
		norm0 = rs.VectorRotate(tan, 90, [0,0,1])*os
		os_pt0 = pt0+norm0

		pt1 = rs.EvaluateCurve(e, p1)
		tan1 = rs.CurveTangent(e, p1)
		norm1 = rs.VectorRotate(tan, 90, [0,0,1])*os
		os_pt1 = pt1+norm1
		
		if rs.IsPointOnSurface(face,os_pt):
			norm = rs.VectorReverse(norm)
			os_pt = pt + norm

			norm0 = rs.VectorReverse(norm0)
			os_pt0 = pt0 + norm0

			norm1 = rs.VectorReverse(norm1)
			os_pt1 = pt1 + norm1

		if (os_sc != 0):
			os_seg = rs.OffsetCurve(seg, os_pt, os_sc*os)
			rs.DeleteObject(seg)
		else:
			# make U
			lseg = rs.AddSubCrv(e, p0, pm)
			rseg = rs.AddSubCrv(e, pm, p1)
			if ind != 0:
				outl = rs.OffsetCurve(lseg, os_pt, os)[0]
				lsln = rs.AddLine(pt0, pt0+norm0*0.1)
				lc = rs.AddCurve([pt0+norm0*0.1,pt+norm*0.1,pt+norm],2)
				rs.JoinCurves([outl,lsln,lc],True)

			if ind != len(params)-2:
				outr = rs.OffsetCurve(rseg, os_pt, os)[0]
				rsln = rs.AddLine(pt1, pt1+norm1*0.1)
				rc = rs.AddCurve([pt1+norm1*0.1,pt+norm*0.1,pt+norm],2)
				rs.JoinCurves([outr,rsln,rc],True)
			rs.DeleteObject(lseg)
			rs.DeleteObject(rseg)

		if ind == 0 and os_sc > 0:
			rs.AddLine(pt0, os_pt0)

		if ind == len(params) -2 and os_sc > 0:
			rs.AddLine(pt1, os_pt1)
		# swap
		if (os_sc == 0.0): os_sc = 1.0
		else: os_sc = 0.0

	rs.DeleteObject(e)

if( __name__ == "__main__" ):
	makeZipperLamp()