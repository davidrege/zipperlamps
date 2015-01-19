import rhinoscriptsyntax as rs
import random

base_srfs = rs.ObjectsByLayer("base")
base_edges = rs.ObjectsByLayer("edges")
base_edge_data = {}
associated_edges = {}
completed_pieces = []

def makeZipperLamp():
	# color edges
	for e in base_edges:
		glen = 0.25
		gcnt = round(rs.CurveLength(e)/glen)
		print(gcnt)
		if gcnt < 10 : gcnt = 10
		#rs.RebuildCurve(e,3,gcnt)
		rs.ObjectColor(e,[random.randrange(0,255),random.randrange(0,255),random.randrange(0,255)])
		seg_len = rs.CurveLength(e)/(gcnt*1.0)
		rs.AddLayer("points")
		rs.CurrentLayer("points")
		pts = rs.DivideCurveEquidistant(e, seg_len,False,True)
		ptobjs = []
		for pt in pts :
			ptobjs.append(rs.AddPoint(pt))
		dom = rs.CurveDomain(e)[1]
		if len(ptobjs) < gcnt:
			ptobjs.append(rs.AddPoint(rs.CurveEndPoint(e)))

		base_edge_data[e] = [-1,ptobjs] 
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

	face = rs.UnrollSurface(bs, False)[0]

	cen = rs.SurfaceAreaCentroid(face)[0]
	ind = 0
	for ae in associated_edges[bs]:
		makeZipper( cen, face, ae, bs)
		ind = ind + 1

	#rs.DeleteObject(face)

	eobjs = rs.ObjectsByLayer(lname)
	ecrvs = []
	for eobj in eobjs:
		if rs.IsCurve(eobj): ecrvs.append(eobj)
	cp = rs.JoinCurves(ecrvs,True)
	completed_pieces.append(cp[0])

def makeZipper( cen, face, base_edge, face3d):
	result = rs.UnrollSurface(face3d,False,[base_edge])
	rs.DeleteObject(result[0])
	e = result[1][0]

	params = []
	dom = rs.CurveDomain(e)[1]
	len2d = rs.CurveLength(e)
	
	points3d = base_edge_data[base_edge][1]
	
	result = rs.UnrollSurface(face3d,False,points3d)
	rs.DeleteObject(result[0])
	points2d = result[1]
	

	for pt2d in points2d :
		param = rs.CurveClosestPoint(e, rs.PointCoordinates(pt2d))
		params.append(param)

	params = sorted(params, key=float)
	direction = base_edge_data[base_edge][0]
	base_edge_data[base_edge][0] = 1 # switch direction for next pass
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
		pos = (p1-p0)*0.05
		# offset
		pt = rs.EvaluateCurve(e, pm)
		pt_back = rs.EvaluateCurve(e, pm-pos)
		pt_forward = rs.EvaluateCurve(e, pm+pos)
		tan = rs.CurveTangent(e, pm)
		norm = rs.VectorRotate(tan, 90, [0,0,1])*os
		os_pt = pt+norm
		test_pt = pt+norm*0.1

		pt0 = rs.EvaluateCurve(e, p0)
		tan0 = rs.CurveTangent(e, p0)
		norm0 = rs.VectorRotate(tan, 90, [0,0,1])*os
		os_pt0 = pt0+norm0

		pt1 = rs.EvaluateCurve(e, p1)
		tan1 = rs.CurveTangent(e, p1)
		norm1 = rs.VectorRotate(tan, 90, [0,0,1])*os
		os_pt1 = pt1+norm1
		
		if rs.IsPointOnSurface(face,test_pt):
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
			lsseg = rs.AddSubCrv(e,p0,pm-pos)
			rseg = rs.AddSubCrv(e, pm, p1)
			rsseg = rs.AddSubCrv(e, pm+pos, p1)
			if ind != 0:
				outl = rs.OffsetCurve(lsseg, os_pt, os)[0]
				lsln = rs.AddLine(pt0, pt0+norm0*0.1)
				lc = rs.AddCurve([pt0+norm0*0.1,pt_back+norm*0.1,pt_back+norm],2)
				rs.JoinCurves([outl,lsln,lc],True)

			if ind != len(params)-2:
				outr = rs.OffsetCurve(rsseg, os_pt, os)[0]
				rsln = rs.AddLine(pt1, pt1+norm1*0.1)
				rc = rs.AddCurve([pt1+norm1*0.1,pt_forward+norm*0.1,pt_forward+norm],2)
				rs.JoinCurves([outr,rsln,rc],True)
			rs.DeleteObject(lseg)
			rs.DeleteObject(rseg)
			rs.DeleteObject(lsseg)
			rs.DeleteObject(rsseg)

		if ind == 0 and os_sc > 0:
			rs.AddLine(pt0, os_pt0)

		if ind == len(params) -2 and os_sc > 0:
			rs.AddLine(pt1, os_pt1)
		# swap
		if (os_sc == 0.0): os_sc = 1.0
		else: os_sc = 0.0

	rs.DeleteObject(e)
	rs.DeleteObjects(points2d)

if( __name__ == "__main__" ):
	makeZipperLamp()