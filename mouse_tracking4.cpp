#include <cv.h>
#include <cvaux.h>
#include <highgui.h>
#include <cvblob.h>
#include <string>

using namespace std;
using namespace cvb;

bool hasEnding (std::string const &fullString, std::string const &ending)
{
    if (fullString.length() >= ending.length()) {
        return (0 == fullString.compare (fullString.length() - ending.length(), ending.length(), ending));
    } else {
        return false;
    }
}


int main(int argc, char** argv) 
{
	/* Declare variables for tracking */
	CvTracks tracks;
	CvCapture* capture;
	double seconds, frameCount = 1;
	bool show_video=false;
	char* filename = "";
	double startFrame = 0;
	string strarg;
	const CvPoint TOPLEFT = cvPoint(0,0);
	const CvPoint BOTTOMRIGHT = cvPoint(80,60);
	const CvScalar BLACK = CV_RGB(0,0,0);

	for (int i = 1; i < argc; i++) 
	{ /* We will iterate over argv[] to get the parameters stored inside.
           * Note that we're starting on 1 because we don't need to know the 
           * path of the program, which is stored in argv[0] */
            if (i != argc) // Check that we haven't finished parsing already
		strarg = argv[i];
		if (strarg.length() > 3)
		{
			if (hasEnding(strarg,".ogg")|hasEnding(strarg,".ogv"))
			{
                   	 // We know the next argument *should* be the filename:
                    		filename = (char*)strarg.c_str();
                	}
		} 
		if (strarg == "-s") 
		{
                    startFrame = atoi(argv[i + 1]);
                }
		if (strarg == "-v")
		{
		    show_video = true;
		}
		//cout << strarg << endl; 
		/*else 
		{
                    std::cout << "Not enough or invalid arguments, please try again.\n";
                    exit(0);
            	}*/
	}
	//cout << "Filename: " << filename << ", Start frame: " << startFrame << ", Show video: " << show_video << "." << endl;
	/* If no argument is given, throw an error. */
	if (argc < 2 or filename == "") {
		fprintf(stderr, "calling sequence: mouse_tracking [-v] videofile.\n");
		fprintf(stderr, "Please provide a video file.\n");
		return -1;
	}
	/* Start capturing 
	if (argc >= 3 || argc == 5) {
		filename=argv[2];
		show_video = true;
	}
	else {
		filename=argv[1];
		show_video = false;
	}*/
	capture = cvCaptureFromFile(filename);
	if (!capture) {
		fprintf(stderr, "Could not open video file.\n");
		return -1;
	}

	/* Get the FPS of the video */
	double fps = cvGetCaptureProperty(capture, CV_CAP_PROP_FPS);
	
	/* Capture the first video frame for initialization */
	//IplImage* frame = cvQueryFrame(capture);

	/* Get the width and height of the video */
	//CvSize size = cvGetSize(frame);

        if( startFrame )
        {
                cvSetCaptureProperty(capture, CV_CAP_PROP_POS_MSEC, startFrame*1000);
        }

	//cout << "Position: " << cvGetCaptureProperty(capture, CV_CAP_PROP_POS_FRAMES) << endl;	
	IplImage* frame = cvQueryFrame(capture);
	cvSaveImage("fme.PNG", frame);
	CvSize size = cvGetSize(frame);
	/* Temporary gray scale images of the same size as the video frames */
	IplImage*	temp = cvCreateImage(size, IPL_DEPTH_8U, 1);
	//IplImage*	temp2 = cvCreateImage(size, IPL_DEPTH_8U, 1);
	IplImage*	all_blobs= cvCreateImage(size, IPL_DEPTH_8U, 3);
	IplImage*	labelImg = cvCreateImage(size, IPL_DEPTH_LABEL, 1);
	cvSet(all_blobs, CV_RGB(0,0,0));

	/* Create windows for videos */
	if (show_video){
		cvNamedWindow("original", 1);
	    cvNamedWindow("foreground", 1);
		cvNamedWindow("mouse_tracking", 1);
		cvNamedWindow("all_blobs", 1);
	}

	/* Parameters for background subtraction. */ 
	CvFGDStatModelParams params;
	params.Lc			= CV_BGFG_FGD_LC; //128
	params.Lcc		= CV_BGFG_FGD_LCC; //64
	params.N1c		= CV_BGFG_FGD_N1C; //15
	params.N2c		= CV_BGFG_FGD_N2C; //25
	params.N1cc		= CV_BGFG_FGD_N1CC; //25
	params.N2cc		= CV_BGFG_FGD_N2CC; //40
	params.delta	= CV_BGFG_FGD_DELTA; //2
	params.alpha1	= CV_BGFG_FGD_ALPHA_1; //0.1
	params.alpha2	= .005; 
	params.alpha3	= CV_BGFG_FGD_ALPHA_3; //0.1
	/* Percentage threshold for background discrimimation */
	params.T			= 0.9f;  //defaults to 0.9
	params.is_obj_without_holes = 1; //ignore holes
	/* Set number of erosion->dilation->erosion cycles o perform */
	params.perform_morphing     = 1;

	/* Mice are small, so the minimal area of objects must be small */
	params.minArea = 10.f; 

	/* Create CvBGStatModel for background subtraction */
	cvRectangle(frame, TOPLEFT,BOTTOMRIGHT, BLACK, -1);
	CvBGStatModel* bgModel = cvCreateFGDStatModel(frame ,&params);
	//CvBlobs blobs;
	/* the data is output in Python syntax */
	cout << "{'Video File':'" << filename << "','Resolution X':" << size.width;
	cout << ",'Resolution Y':" << size.height << ",'FPS':" << fps;
	cout << ",'Tracks by Frame':[" << endl;

	/* loop through all frames of the video */
	while (frame = cvQueryFrame(capture)) {
		if (show_video)
			cvShowImage("original", frame); /* Show the original video */

		/* Update background model */
		cvRectangle(frame, TOPLEFT,BOTTOMRIGHT, BLACK, -1);
		cvUpdateBGStatModel(frame, bgModel);

		/* Apply the median filter to eliminate blobs too small to be mice*/
		cvSmooth(bgModel->foreground, temp, CV_MEDIAN, 5);

		/* dilate the image to merge blobs that belong to the same mouse */
		//cvDilate(temp, temp, NULL, 2);
		//cvErode(temp, temp, NULL, 1);
		//cvSmooth(temp, temp2, CV_MEDIAN, 3); 
		/* erode the image to undo size changes related to dilation */

		//cvSmooth(temp, temp2, CV_MEDIAN, 3);
		//cvDilate(temp, temp, NULL, 10);
		//cvErode(temp, temp, NULL, 10);
 
		if (show_video) 
			cvShowImage("foreground", temp); /* Show the mouse blobs */

		/* Calculate how far we are into the video in seconds */
		seconds = frameCount/fps;

		/* Detect and label blobs */
		CvBlobs blobs;
		unsigned int result = cvLabel(temp, labelImg, blobs);

		/* Filter blobs that are either too small or too large*/
		cvFilterByArea(blobs, 10, 4000);
		/* Update the tracks with new blob information */
		cvUpdateTracks(blobs, tracks, 8., 2);

		/* output the track information */
		if(tracks.size() > 0){
			cout << "{'Frame Number':" << frameCount << "," << "'Tracks':[";
			for (CvTracks::const_iterator it=tracks.begin(); it!=tracks.end(); ++it){
				if (it->second->inactive==0)
                                {
                                  cout << "{'Area':" << blobs.find(it->second->label)-> second ->area << ",";
                                  //cout << "{'Contour Area':" << cvConvertChainCodesToPolygon(blobs.find(it->second->label)->second->contour.chainCodesi.begin())<< ",";
                                }
                                else 
                                  cout << "{'Area':0,";
                                cout << "'Track Number':" << it->second->id << ",";
				cout << "'Lifetime':" << it->second->lifetime << ",";
				cout << "'Frames Active':" << it->second->active << ",";
				cout << "'Frames Inactive':" << it->second->inactive << ",";
				cout << "'X':" << it->second->centroid.x << ",";
				cout << "'Y':" << it->second->centroid.y << "},";
				//if(it==tracks.end()) cout << "]"; else cout << ",";
			}
			cout << "]}," << endl;
			if (show_video){
				cvRenderTracks(tracks, frame, frame, CV_TRACK_RENDER_ID|CV_TRACK_RENDER_BOUNDING_BOX);
				cvRenderTracks(tracks, all_blobs, all_blobs, CV_TRACK_RENDER_ID|CV_TRACK_RENDER_BOUNDING_BOX);
			}
			/*
			// save a still with 2 blobs
			if(tracks.size()>1)
			{
			cvSaveImage("tracked.PNG",frame);
			cvSaveImage("foreground.PNG",bgModel->foreground);
			cvSaveImage("cleanedup.PNG",temp);
			return 0;
			}
			*/
		}
		//save a still from first frame
		/*if(frameCount == 1){
			//Need to add filename in here
			string frameName = filename;
			frameName.erase(frameName.length()-4, frameName.length());
			frameName += "frame1.PNG";
			const char* str = frameName.c_str ();
			cvSaveImage(str,frame);
		}*/
		if (show_video) {
			cvShowImage("mouse_tracking",frame); /* Show the original video with tracked mice */
			cvShowImage("all_blobs",all_blobs); /* Show the original video with tracked mice */
		}

		/* Release current blob information */
		cvReleaseBlobs(blobs);

		/* update the frame counter */
		frameCount++;

		if (show_video) { cvWaitKey(2); }
	}

	/* close the list of tracks */
	cout << "]}" << endl << endl;

	/* After we're all done, clean up */
	if(show_video){
		cvDestroyWindow("original");
		cvDestroyWindow("foreground");
		cvDestroyWindow("test_tracking");
		cvDestroyWindow("all_blobs");
	}
	cvReleaseImage(&temp);
	cvReleaseImage(&labelImg);
	cvReleaseBGStatModel(&bgModel);
	cvReleaseCapture(&capture);
	cvReleaseTracks(tracks);
 
	return 0;
}

