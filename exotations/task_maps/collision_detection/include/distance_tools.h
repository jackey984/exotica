/*
 * distance_tools.h
 *
 *  Created on: 8 Aug 2014
 *      Author: yiming
 */

#ifndef DISTANCE_TOOLS_H_
#define DISTANCE_TOOLS_H_
namespace exotica
{
	//	\brief	Extra distance information that might be used for EXOTica collision detection
	struct DistancePair
	{
			DistancePair() :
					id1(-1), id2(-1), hasNorm(false), d(100), isLink2(false), cost(0.0)
			{

			}

			//	\brief	The names of objects. Usually o1 is segment of robot and o2 is the obstacle
			std::string o1;
			std::string o2;

			//	\brief	Object centres
			Eigen::Vector3d c1;
			Eigen::Vector3d c2;

			//	\brief	Closest points
			Eigen::Vector3d p1;
			Eigen::Vector3d p2;

			//	\brief	IDs of closest points (for mesh data)
			int id1;
			int id2;

			//	\brief	Indicates the type: robot link (true) or environmental object (false)
			bool isLink2;

			//	\brief	Normal vectors (to object centre)
			Eigen::Vector3d norm1;
			Eigen::Vector3d norm2;

			double d;	// Distance
			double cost;
			bool hasNorm;
	};
	struct DistanceInfo
	{
		private:
			double overall_closest_;
			double initialised_;
			boost::mutex dist_lock_;
			bool multi_objs_;
		public:
			DistanceInfo() :
					overall_closest_(0), initialised_(false), multi_objs_(true)
			{
			}

			//	\Map between links and distance pairs
			std::map<std::string, std::vector<DistancePair> > link_dist_map_;

			//	\Initialise the map
			bool initialise(const std::vector<std::string> & links)
			{
				link_dist_map_.clear();
				for (int i = 0; i < links.size(); i++)
					link_dist_map_[links[i]].clear();
				initialised_ = true;
				return true;
			}
			//	\Set the distance
			bool setDistance(const DistancePair & dist_pair)
			{
				boost::mutex::scoped_lock(dist_lock_);
				if (!initialised_)
					return false;
				if (link_dist_map_.find(dist_pair.o1) == link_dist_map_.end())
					return false;
				if (!multi_objs_)
				{
					if (link_dist_map_.at(dist_pair.o1).size() == 0)
						link_dist_map_.at(dist_pair.o1).push_back(dist_pair);
					else if (link_dist_map_.at(dist_pair.o1)[0].d > dist_pair.d)
						link_dist_map_.at(dist_pair.o1)[0] = dist_pair;
				}
				else
					link_dist_map_.at(dist_pair.o1).push_back(dist_pair);
				return true;
			}

			// \Resetall distances
			bool resetDistance()
			{
				if (!initialised_)
					return false;
				for (auto & it : link_dist_map_)
					it.second.clear();
				return true;
			}

			//	\Get distance of particular link
			bool getDistance(const std::string & link, std::vector<DistancePair> & dist_pair)
			{
				boost::mutex::scoped_lock(dist_lock_);
				if (!initialised_)
					return false;
				if (link_dist_map_.find(link) == link_dist_map_.end())
					return false;
				dist_pair = link_dist_map_.at(link);
				return true;
			}

			//	\Get overall closest distance
			double ClosestDistance()
			{
				if (!initialised_)
					return 0;
				else
					return overall_closest_;
			}

			//	\Check validation
			bool isInitialised()
			{
				return initialised_;
			}

			//	\Invalidates
			void invalidate()
			{
				overall_closest_ = 0;
				link_dist_map_.clear();
				initialised_ = false;
			}

			//	\Check existance
			bool hasLink(const std::string & link)
			{
				if (link_dist_map_.find(link) != link_dist_map_.end())
					return true;
				else
					return false;
			}

			void print()
			{
				if (!initialised_)
					std::cout << "Distance information is not valid" << std::endl;
				else
				{
					std::cout << "Distance information:" << std::endl;
					for (auto & it : link_dist_map_)
					{
						for (int i = 0; i < it.second.size(); i++)
							std::cout << "Distance between [" << it.first << "] and ["
									<< it.second[i].o2 << "] is " << it.second[i].d << std::endl;
					}

				}
			}

	};
}

#endif /* DISTANCE_TOOLS_H_ */
